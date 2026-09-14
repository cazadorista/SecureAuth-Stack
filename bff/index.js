const express = require('express');
const session = require('express-session');
const { Issuer, custom, generators } = require('openid-client');

custom.setHttpOptionsDefaults({
  timeout: 10000,
});

const app = express();
const PORT = 3000;

app.set('trust proxy', 1);

app.use(express.json());

app.use(session({
  name: 'SID',
  secret: process.env.SESSION_SECRET || 'super_tajny_sekret_sesji',
  resave: false,
  saveUninitialized: false,
  cookie: {
    httpOnly: true,
    secure: false, // DEV ONLY: False on local environment for browser allowing http/https cookies
    sameSite: 'lax',
    path: '/'
  }
}));

let client;

async function initOpenId() {
  const internalUrl = process.env.KEYCLOAK_INTERNAL_URL || 'http://keycloak:8080';
  const realm = process.env.REALM || 'playground';
  const discoveryUrl = `${internalUrl}/realms/${realm}`;

  try {
    console.log(`Pobieranie metadanych Keycloak z: ${discoveryUrl}...`);
    const keycloakIssuer = await Issuer.discover(discoveryUrl);

    client = new keycloakIssuer.Client({
      client_id: process.env.CLIENT_ID,
      client_secret: process.env.CLIENT_SECRET,
      redirect_uris: ['https://localhost/api/auth/callback'],
      response_types: ['code']
    });

    console.log('✅ Klient OpenID poprawnie zainicjalizowany.');
  } catch (err) {
    console.error('❌ Błąd inicjalizacji OpenID w BFF:', err.message);
  }
}

// Login
app.get('/api/auth/login', (req, res) => {
  try {
    if (!client) {
      return res.status(503).send('Serwis autoryzacji BFF jeszcze się inicjalizuje, odśwież za chwilę stronę.');
    }

    const redirectUri = req.query.redirect || 'https://localhost/';
    req.session.returnTo = redirectUri;

    const code_verifier = generators.codeVerifier();
    const code_challenge = generators.codeChallenge(code_verifier);
    req.session.code_verifier = code_verifier;

    const rawUrl = client.authorizationUrl({
      scope: 'openid profile email',
      redirect_uri: 'https://localhost/api/auth/callback',
      code_challenge,
      code_challenge_method: 'S256'
    });

    const internalUrl = process.env.KEYCLOAK_INTERNAL_URL || 'http://keycloak:8080';
    const externalUrl = process.env.KEYCLOAK_EXTERNAL_URL || 'https://auth.localhost';

    req.session.save((err) => {
      if (err) console.error('Błąd zapisu sesji:', err);
      res.redirect(rawUrl.replace(internalUrl, externalUrl));
    });
  } catch (err) {
    console.error('Błąd w /api/auth/login:', err);
    res.status(500).send('Błąd generowania przekierowania autoryzacji: ' + err.message);
  }
});

// Callback
app.get('/api/auth/callback', async (req, res) => {
  try {
    if (!client) {
      return res.status(503).send('BFF Client not ready');
    }

    const params = client.callbackParams(req);
    const code_verifier = req.session ? req.session.code_verifier : null;

    if (!code_verifier) {
      throw new Error('Brak code_verifier w sesji! Upewnij się, że ciasteczka sesyjne są przekazywane.');
    }

    const tokenSet = await client.callback(
      'https://localhost/api/auth/callback',
      params,
      { code_verifier }
    );

    delete req.session.code_verifier;
    req.session.tokens = tokenSet;
    req.session.user = tokenSet.claims();

    const returnTo = req.session.returnTo || 'https://localhost/';
    delete req.session.returnTo;

    req.session.save(() => {
      res.redirect(returnTo);
    });
  } catch (err) {
    console.error('Błąd autoryzacji w BFF:', err);
    res.status(500).send('Authentication failed: ' + err.message);
  }
});

app.get('/api/auth/me', (req, res) => {
  if (req.session && req.session.user) {
    return res.json({
      authenticated: true,
      user: req.session.user
    });
  }
  res.json({ authenticated: false });
});

app.get('/api/auth/logout', (req, res) => {
  const idToken = req.session?.tokens?.id_token;

  req.session.destroy(() => {
    res.clearCookie('SID', { path: '/' });

    const externalUrl = process.env.KEYCLOAK_EXTERNAL_URL || 'https://auth.localhost';
    const realm = process.env.REALM || 'playground';
    const postLogoutRedirectUri = encodeURIComponent('https://localhost/');

    let logoutUrl = `${externalUrl}/realms/${realm}/protocol/openid-connect/logout?post_logout_redirect_uri=${postLogoutRedirectUri}`;

    if (idToken) {
      logoutUrl += `&id_token_hint=${idToken}`;
    } else {
      logoutUrl += `&client_id=${process.env.CLIENT_ID || 'bff-client'}`;
    }

    res.redirect(logoutUrl);
  });
});

initOpenId().then(() => {
  app.listen(PORT, () => console.log(`BFF Service running on port ${PORT}`));
});
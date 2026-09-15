const express = require('express');
const session = require('express-session');
const { Issuer, custom, generators } = require('openid-client');
const { createClient } = require('redis');
const { RedisStore } = require('connect-redis');

custom.setHttpOptionsDefaults({
  timeout: 10000,
});

const app = express();
const PORT = 3000;

const redisClient = createClient({
  url: process.env.REDIS_URL
});

redisClient.connect().catch(console.error);

app.set('trust proxy', 1);

app.use(express.json());

app.use(session({
  store: new RedisStore({ client: redisClient, prefix: 'bff_sess:', ttl: 86400 }),
  name: 'SID',
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    httpOnly: true,
    secure: false, // DEV ONLY: False on local environment for browser allowing http/https cookies
    sameSite: 'lax',
    path: '/',
    domain: process.env.COOKIE_DOMAIN
  }
}));

let client;

async function initOpenId() {
  const internalUrl = process.env.KEYCLOAK_INTERNAL_URL;
  const realm = process.env.REALM;
  const discoveryUrl = `${internalUrl}/realms/${realm}`;

  try {
    console.log(`Pobieranie metadanych Keycloak z: ${discoveryUrl}...`);
    const keycloakIssuer = await Issuer.discover(discoveryUrl);

    client = new keycloakIssuer.Client({
      client_id: process.env.CLIENT_ID,
      client_secret: process.env.CLIENT_SECRET,
      redirect_uris: [`https://${process.env.DOMAIN_APP}/api/auth/callback`],
      response_types: ['code']
    });

    console.log('✅ Klient OpenID poprawnie zainicjalizowany.');
  } catch (err) {
    console.error('❌ Błąd inicjalizacji OpenID w BFF:', err.message);
  }
}

// Login
app.get('/api/auth/login', async (req, res) => {
  try {
    if (!client) {
      return res.status(503).send('Serwis autoryzacji BFF jeszcze się inicjalizuje, odśwież za chwilę stronę.');
    }

    const redirectUri = req.query.redirect;
    req.session.returnTo = redirectUri;

    const code_verifier = generators.codeVerifier();
    const code_challenge = generators.codeChallenge(code_verifier);
    req.session.code_verifier = code_verifier;

    const rawUrl = client.authorizationUrl({
      scope: 'openid profile email',
      redirect_uri: `https://${process.env.DOMAIN_APP}/api/auth/callback`,
      code_challenge,
      code_challenge_method: 'S256'
    });

    const internalUrl = process.env.KEYCLOAK_INTERNAL_URL;
    const externalUrl = process.env.KEYCLOAK_EXTERNAL_URL;

    if (!internalUrl || !externalUrl) {
      return res.status(500).send('Błąd konfiguracji zmiennych środowiskowych KEYCLOAK_*');
    }

    const targetUrl = rawUrl.replace(internalUrl, externalUrl);

    req.session.save((err) => {
      if (err) {
        return res.status(500).send('Błąd zapisu sesji w Redis');
      }
      return res.redirect(targetUrl);
    });
  } catch (err) {
    console.error('Błąd w /api/auth/login:', err);
    return res.status(500).send('Błąd generowania przekierowania autoryzacji: ' + err.message);
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
      `https://${process.env.DOMAIN_APP}/api/auth/callback`,
      params,
      { code_verifier }
    );

    delete req.session.code_verifier;
    req.session.tokens = tokenSet;
    req.session.user = tokenSet.claims();

    const returnTo = req.session.returnTo;
    delete req.session.returnTo;

    req.session.save((err) => {
      if (err) {
        console.error('Błąd zapisu sesji w Redis po zalogowaniu:', err);
        return res.status(500).send('Błąd zapisu sesji');
      }
      console.log(`Zalogowano pomyślnie. Przekierowuję na: ${returnTo}`);
      return res.redirect(returnTo);
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

    const externalUrl = process.env.KEYCLOAK_EXTERNAL_URL;
    const realm = process.env.REALM;
    const postLogoutRedirectUri = encodeURIComponent(`https://${process.env.DOMAIN_APP}/`);

    let logoutUrl = `${externalUrl}/realms/${realm}/protocol/openid-connect/logout?post_logout_redirect_uri=${postLogoutRedirectUri}`;

    if (idToken) {
      logoutUrl += `&id_token_hint=${idToken}`;
    } else {
      logoutUrl += `&client_id=${process.env.CLIENT_ID}`;
    }

    res.redirect(logoutUrl);
  });
});

initOpenId().then(() => {
  app.listen(PORT, () => console.log(`BFF Service running on port ${PORT}`));
});
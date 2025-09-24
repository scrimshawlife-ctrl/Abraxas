import session from "express-session";
import passport from "passport";
import { Strategy as GoogleStrategy } from "passport-google-oauth20";
import db from "./db.js";
import { v4 as uuidv4 } from "uuid";

export function sessionMiddleware() {
  return session({
    secret: process.env.SESSION_SECRET || "abraxas-session-secret",
    resave: false,
    saveUninitialized: false,
    cookie: { secure: false, maxAge: 24 * 60 * 60 * 1000 } // 24 hours
  });
}

export function googlePassport() {
  passport.use(new GoogleStrategy({
    clientID: process.env.GOOGLE_CLIENT_ID,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    callbackURL: process.env.OAUTH_CALLBACK_URL || "/auth/google/callback"
  }, async (accessToken, refreshToken, profile, done) => {
    try {
      let user = db.prepare("SELECT * FROM users WHERE email = ?").get(profile.emails[0].value);
      
      if (!user) {
        const userId = uuidv4();
        db.prepare(`
          INSERT INTO users (id, email, name, picture, created_at) 
          VALUES (?, ?, ?, ?, ?)
        `).run(
          userId,
          profile.emails[0].value,
          profile.displayName,
          profile.photos[0]?.value,
          Date.now()
        );
        user = { id: userId, email: profile.emails[0].value, name: profile.displayName };
      }
      
      return done(null, user);
    } catch (error) {
      return done(error, null);
    }
  }));

  passport.serializeUser((user, done) => done(null, user.id));
  passport.deserializeUser((id, done) => {
    const user = db.prepare("SELECT * FROM users WHERE id = ?").get(id);
    done(null, user);
  });

  return passport;
}

export function ensureAuthed(req, res, next) {
  if (req.isAuthenticated()) return next();
  if (req.path.startsWith("/api/")) return res.status(401).json({ error: "authentication required" });
  res.redirect("/login");
}
import { Button, Divider, Grid } from "@material-ui/core";
import { observer } from "mobx-react-lite";
import React, { useEffect, useState } from "react";
import { GoogleLogin } from "react-google-login";
import { BrowserRouter as Router, Route, Switch } from "react-router-dom";
import v from "voca";

import "./App.css";
import logo from "./App.logo.png";
import sorry_gif from "./sorry.gif";
import { AccountProfileContent } from "diaas/Account.js";
import { AnalyticsContent } from "diaas/Analytics";
import { TextField, useFormValue } from "diaas/form.js";
import { JobsContent } from "diaas/Jobs";
import { AppNavigation, AppSplash } from "diaas/layout.js";
import { ModelsContent } from "diaas/Models.js";
import { ModulesContent } from "diaas/Modules";
import { SourcesContent } from "diaas/Sources";
import { AppState, useAppState } from "diaas/state.js";
import { StoreContent } from "diaas/Store.js";
import { ThemeProvider } from "diaas/Theme.js";
import { HCenter } from "diaas/ui.js";
import { ignore } from "diaas/utils.js";

const Loading = () => {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let t = 0;
    const interval = setInterval(() => {
      t = (t + 1) % 3;
      setTick(t);
    }, 600);
    return () => {
      clearInterval(interval);
    };
  }, []);
  return (
    <div className="App" style={{ textAlign: "center" }}>
      <header
        style={{
          backgroundColor: "#2e3631",
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "calc(10px + 2vmin)",
          color: "white",
        }}
      >
        <img style={{ pointerEvents: "none", width: "420px" }} src={logo} alt="Caravel WorkBench Logo" />
        <div style={{ position: "relative", top: "0px", left: "0px" }}>
          <p style={{ color: "#2e3631", opacity: 0 }}>Loading the Caravel WorkBench, please wait...</p>
          <p style={{ position: "absolute", top: "0px", left: "0px" }}>
            Loading the Caravel WorkBench, please wait
            <span>{v.repeat(".", tick + 1)}</span>
          </p>
        </div>
        <div style={{ position: "absolute", bottom: "0px", right: "0px" }}>
          (debug: {window.DIAAS.DEPLOYMENT_ENVIRONMENT})
        </div>
      </header>
    </div>
  );
};

const GoogleLoginButton = ({ loginHandler, loginInProgress }) => {
  const googleLogin = (u) => {
    loginInProgress.v = true;
    loginHandler({ google: { id_token: u.getAuthResponse(false).id_token } });
  };

  const googleFailure = (r) => {
    console.log("GOOGLE FAIL:", r);
    alert(JSON.stringify(r));
  };

  return (
    <GoogleLogin
      clientId={window.DIAAS.AUTH_GOOGLE_CLIENT_ID}
      disabled={loginInProgress.v}
      buttonText="Login via Google"
      onSuccess={googleLogin}
      onFailure={googleFailure}
      cookiePolicy={"single_host_origin"}
    />
  );
};

const EmailLoginForm = ({ loginHandler, loginInProgress }) => {
  const email = useFormValue("", { transform: (e) => v.trim(e) });
  const emailIsValid = v.trim(email.v).length > 0 && v.search(email.v, /.@.+[.].+/) > -1;

  const submit = (e) => {
    e.preventDefault();
    loginHandler({ email: email.v });
  };

  return (
    <form onSubmit={submit}>
      <Grid container>
        <Grid item xs={12}>
          <HCenter>
            <TextField label="email" autoFocus={true} value={email} disabled={loginInProgress.v} />
          </HCenter>
        </Grid>
        <Grid item xs={12}>
          <HCenter pt={2}>
            <Button variant="contained" color="primary" disabled={!emailIsValid || loginInProgress.v} onClick={submit}>
              Login via Magic Link
            </Button>
          </HCenter>
        </Grid>
      </Grid>
    </form>
  );
};

const Login = observer(() => {
  const state = useAppState();
  const loginInProgress = useFormValue(false);

  const loginHandler = (data) => {
    state.login(data).then(() => {
      loginInProgress.v = false;
    });
  };

  return (
    <div style={{ position: "static" }}>
      <AppSplash>
        <Grid container>
          <Grid item xs={12}>
            <EmailLoginForm loginHandler={loginHandler} loginInProgress={loginInProgress} />
          </Grid>
          <Grid item xs={12}>
            <HCenter my={2}>
              <Divider width="33%" />
            </HCenter>
          </Grid>
          <Grid item xs={12}>
            <HCenter>
              <GoogleLoginButton loginHandler={loginHandler} loginInProgress={loginInProgress} />
            </HCenter>
          </Grid>
        </Grid>
      </AppSplash>
    </div>
  );
});

const AppContent = () => (
  <div style={{ position: "static" }}>
    <Router>
      <AppNavigation>
        <Switch>
          <Route path="/modules/">
            <ModulesContent />
          </Route>
          <Route path="/sources/">
            <SourcesContent />
          </Route>
          <Route path="/models/">
            <ModelsContent />
          </Route>
          <Route path="/store/">
            <StoreContent />
          </Route>
          <Route path="/jobs/">
            <JobsContent />
          </Route>
          <Route path="/analytics/">
            <AnalyticsContent />
          </Route>
          <Route path="/catalog/">Catalog</Route>
          <Route path="/monitoring/">Monitoring</Route>
          <Route path="/settings/">Settings</Route>
          <Route path="/account/profile">
            <AccountProfileContent />
          </Route>
          <Route path="/">
            <p>Welcome to Caravel.</p>
          </Route>
        </Switch>
      </AppNavigation>
    </Router>
  </div>
);

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, details: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, details: { title: "Error", message: "" + error } };
  }

  componentDidCatch(error, errorInfo) {
    // NOTE send to sentry 20210305:mb
    ignore(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <FatalError details={this.state.details} />;
    } else {
      return this.props.children;
    }
  }
}

const FatalError = ({ details }) => {
  let toClipBoard = null;
  if ("clipboard" in navigator) {
    toClipBoard = () => navigator.clipboard.writeText(details.title + "\n\n" + details.message);
  } else {
    toClipBoard = false;
  }
  return (
    <HCenter>
      <Grid container>
        <Grid item xs={12}>
          <HCenter>
            <img src={sorry_gif} alt="borken." />
          </HCenter>
        </Grid>
        <Grid item xs={12}>
          <HCenter>{details.title}</HCenter>
          <HCenter>
            <pre>{details.message}</pre>
          </HCenter>
          {toClipBoard && (
            <HCenter>
              <Button variant="contained" color="primary" onClick={toClipBoard}>
                Copy error to clipboard
              </Button>
            </HCenter>
          )}
        </Grid>
      </Grid>
    </HCenter>
  );
};

const App = observer(() => {
  const state = useAppState();
  useEffect(() => {
    state.initialize();
  }, [state]);
  if (state.fatalError) {
    return <FatalError details={state.fatalError} />;
  } else {
    if (!state.initialized) {
      return <Loading />;
    } else if (state.user) {
      return <AppContent />;
    } else {
      return <Login />;
    }
  }
});

export const Root = () => (
  <React.StrictMode>
    <ThemeProvider>
      <AppState>
        <ErrorBoundary>
          <App />
        </ErrorBoundary>
      </AppState>
    </ThemeProvider>
  </React.StrictMode>
);

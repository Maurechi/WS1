import { Button, Grid } from "@material-ui/core";
import { observer } from "mobx-react-lite";
import React, { useEffect, useState } from "react";
import { BrowserRouter as Router, Route, Switch } from "react-router-dom";
import v from "voca";

import "./App.css";
import logo from "./App.logo.png";
import { AccountProfileContent } from "diaas/Account.js";
import { AnalyticsContent } from "diaas/Analytics";
import { TextField, useFormValue } from "diaas/form.js";
import { JobsContent } from "diaas/Jobs";
import { AppNavigation, AppSplash } from "diaas/layout.js";
import { ModulesContent } from "diaas/Modules";
import { SourcesContent } from "diaas/Sources";
import { AppState, useAppState } from "diaas/state.js";
import { ThemeProvider } from "diaas/Theme.js";
import { HCenter } from "diaas/utils.js";
import { WorkbenchContent } from "diaas/Workbench.js";

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
      </header>
    </div>
  );
};

const Login = observer(() => {
  const state = useAppState();
  const email = useFormValue("", { transform: (e) => v.trim(e) });
  const isValid = v.trim(email.v).length > 0 && v.search(email.v, /.@.+[.].+/) > -1;
  const submit = (e) => {
    e.preventDefault();
    state.login(email.v);
  };
  return (
    <div style={{ position: "static" }}>
      <AppSplash>
        <form onSubmit={submit}>
          <Grid container>
            <Grid item xs={12}>
              <HCenter>
                <TextField label="email" autoFocus={true} value={email} />
              </HCenter>
            </Grid>
            <Grid item xs={12}>
              <HCenter pt={2}>
                <Button variant="contained" color="primary" disabled={!isValid} onClick={submit}>
                  Login
                </Button>
              </HCenter>
            </Grid>
          </Grid>
        </form>
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
          <Route path="/workbench/">
            <WorkbenchContent />
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

const App = observer(() => {
  const state = useAppState();
  useEffect(() => {
    state.initialize();
  }, [state]);
  if (!state.initialized) {
    return <Loading />;
  } else if (state.user) {
    return <AppContent />;
  } else {
    return <Login />;
  }
});

export const Root = () => (
  <React.StrictMode>
    <ThemeProvider>
      <AppState>
        <App />
      </AppState>
    </ThemeProvider>
  </React.StrictMode>
);

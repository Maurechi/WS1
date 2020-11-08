import { Button, Grid } from "@material-ui/core";
import { createMuiTheme, ThemeProvider } from "@material-ui/core/styles";
import { observer } from "mobx-react-lite";
import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom";
import v from "voca";

import "./index.css";
import logo from "./diaas-logo.png";
import reportWebVitals from "./reportWebVitals";
import { TextInput, useFormValue } from "diaas/form.js";
import { AppNavigation, AppSplash, HCenter } from "diaas/layout.js";
import { AppState, useAppState } from "diaas/state.js";

const theme = createMuiTheme({
  palette: {
    primary: {
      main: "#2e3631",
    },
    secondary: {
      main: "#4db96d",
    },
  },
});

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
        <img style={{ pointerEvents: "none", width: "420px" }} src={logo} alt="DIAAS WorkBench Logo" />
        <div style={{ position: "relative", top: "0px", left: "0px" }}>
          <p style={{ color: "#2e3631", opacity: 0 }}>Loading the DIAAS WorkBench, please wait...</p>
          <p style={{ position: "absolute", top: "0px", left: "0px" }}>
            Loading the DIAAS WorkBench, please wait
            <span>{v.repeat(".", tick + 1)}</span>
          </p>
        </div>
      </header>
    </div>
  );
};

const Login = observer(() => {
  const state = useAppState();
  const email = useFormValue();
  const isValid = v.trim(email.v).length > 0 && v.search(email.v, /.@.+[.].+/) > -1;
  console.log("Login state", state);
  const submit = () => {
    state.login(email.v);
  };
  return (
    <div style={{ position: "static" }}>
      <AppSplash>
        <Grid container>
          <Grid item xs={12}>
            <HCenter>
              <TextInput label="email" autoFocus={true} value={email} />
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
      </AppSplash>
    </div>
  );
});

const AppContent = () => (
  <div style={{ position: "static" }}>
    <AppNavigation>
      <p>DIAAS WorkBench.</p>
    </AppNavigation>
  </div>
);

const App = observer(() => {
  const state = useAppState();
  console.log("App state", state);
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

ReactDOM.render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <AppState>
        <App />
      </AppState>
    </ThemeProvider>
  </React.StrictMode>,
  document.getElementById("root")
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals(console.log);

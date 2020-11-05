import { createMuiTheme, ThemeProvider } from "@material-ui/core/styles";
import { observer } from "mobx-react-lite";
import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom";
import v from "voca";

import "./index.css";
import logo from "./diaas-logo.png";
import reportWebVitals from "./reportWebVitals";
import { Navigation } from "diaas/navigation";
import { STATE } from "diaas/state.js";

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

const Login = () => <p>Login with google.</p>;

const App = () => (
  <div style={{ position: "static" }}>
    <Navigation>
      <p>DIAAS WorkBench.</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
      <p>1</p>
    </Navigation>
  </div>
);

const Splash = observer(({ state }) => {
  if (!state.isInitialized()) {
    state.initialize();
    return <Loading />;
  } else if (!state.hasUser()) {
    return <Login />;
  } else {
    return <App />;
  }
});

ReactDOM.render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <Splash state={STATE} />
    </ThemeProvider>
  </React.StrictMode>,
  document.getElementById("root")
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals(console.log);

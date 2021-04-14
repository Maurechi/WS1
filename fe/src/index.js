import * as Sentry from "@sentry/react";
import React from "react";
import ReactDOM from "react-dom";

import reportWebVitals from "./reportWebVitals";
import { Root } from "diaas/App.js";
import { logIt } from "diaas/utils.js";

if (window.DIAAS.ENABLE_SENTRY === "true") {
  Sentry.init(
    logIt("Sentry config is", {
      dsn: window.DIAAS.SENTRY_DSN,
      release: window.DIAAS.SENTRY_RELEASE,
      environment: window.DIAAS.SENTRY_ENVIRONMENT,
    })
  );
}

ReactDOM.render(<Root />, document.getElementById("root"));

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
if (window.DIAAS.ENABLE_WEB_VITALS === "true") {
  reportWebVitals(console.log);
}

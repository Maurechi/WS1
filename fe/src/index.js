import * as Sentry from "@sentry/react";
import React from "react";
import ReactDOM from "react-dom";

import reportWebVitals from "./reportWebVitals";
import { Root } from "diaas/App.js";
import { CONFIG } from "diaas/state.js";
import { logIt } from "diaas/utils.js";

if (CONFIG.ENABLE_SENTRY === "true") {
  Sentry.init(
    logIt("Sentry config is", {
      dsn: CONFIG.SENTRY_DSN,
      release: CONFIG.SENTRY_RELEASE,
      environment: CONFIG.SENTRY_ENVIRONMENT,
    })
  );
}

ReactDOM.render(<Root />, document.getElementById("root"));

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
if (CONFIG.ENABLE_WEB_VITALS === "true") {
  reportWebVitals(console.log);
}

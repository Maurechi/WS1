import { Button } from "@material-ui/core";
import React, { useState } from "react";

export const ActionButton = ({ onClick, children }) => {
  const [state, setState] = useState("idle");
  const buttonOnClick = () => {
    setState("busy");
    Promise.resolve(onClick()).then((res) => {
      setState("idle");
      return res;
    });
  };
  return (
    <Button
      onClick={buttonOnClick}
      variant="contained"
      color={state === "idle" ? "primary" : "secondary"}
      disabled={state !== "idle"}
    >
      {children}
    </Button>
  );
};

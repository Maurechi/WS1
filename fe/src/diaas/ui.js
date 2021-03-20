import { Box, Button } from "@material-ui/core";
import _ from "lodash";
import React, { useState } from "react";
import { useHistory } from "react-router-dom";

export const StandardButton = ({ variant = "contained", color = "secondary", style, children, ...buttonProps }) => {
  style = Object.assign({}, style);
  if (!("fontWeight" in style)) {
    style.fontWeight = 800;
  }
  if (!("textTransform" in style)) {
    style.textTransform = "none";
  }

  return (
    <Button variant={variant} color={color} {...buttonProps} style={style}>
      {children}
    </Button>
  );
};

export const ButtonLink = ({ target, children, onClick: callerOnClick, ...buttonProps }) => {
  const history = useHistory();
  const onClick = (e) => {
    return Promise.resolve(callerOnClick ? callerOnClick() : null).then((res) => {
      e.preventDefault();
      history.push(target);
      return res;
    });
  };
  return (
    <StandardButton onClick={onClick} {...buttonProps}>
      {children}
    </StandardButton>
  );
};

// If Box spacking properties are passed wrap the caller in a Box
export const wrapInBox = (Component) => {
  return (allProps) => {
    const boxProps = {};
    const compProps = {};
    const spacingProps = ["m", "mx", "my", "mt", "mb", "ml", "mr", "p", "px", "py", "pt", "pb", "pl", "pr"];
    for (const prop in allProps) {
      if (_.includes(spacingProps, prop)) {
        boxProps[prop] = allProps[prop];
      } else {
        compProps[prop] = allProps[prop];
      }
    }
    if (boxProps) {
      return <Box {...boxProps}>{Component(compProps)}</Box>;
    } else {
      return Component(compProps);
    }
  };
};

export const ActionButton = wrapInBox(({ onClick, disabled = false, children, color = "secondary" }) => {
  const [state, setState] = useState("idle");
  const buttonOnClick = () => {
    setState("busy");
    Promise.resolve(onClick()).then((res) => {
      setState("idle");
      return res;
    });
  };
  const isIdle = state === "idle";
  return (
    <StandardButton onClick={buttonOnClick} color={isIdle ? color : "inherit"} disabled={!isIdle || disabled}>
      {children}
    </StandardButton>
  );
});

export const CenterContent = ({ children }) => (
  <Box display="flex" style={{ width: "100%" }} justifyContent="center">
    <Box>{children}</Box>
  </Box>
);

export const HCenter = ({ children, ...BoxProps }) => (
  <Box display="flex" width="100%" justifyContent="center" {...BoxProps}>
    {children}
  </Box>
);

export const VCenter = ({ children, ...BoxProps }) => (
  <Box display="flex" width="100%" alignItems="center" {...BoxProps}>
    {children}
  </Box>
);

export const NotFound = ({ children }) => (
  <Box style={{ width: "100%" }}>
    <HCenter>Not Found</HCenter>
    <Box>{children}</Box>
  </Box>
);

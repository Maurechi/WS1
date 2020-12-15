import { Box, Button } from "@material-ui/core";
import React from "react";
import { useHistory } from "react-router-dom";

export const ButtonLink = ({ target, children, ...buttonProps }) => {
  const history = useHistory();
  const onClick = (e) => {
    e.preventDefault();
    history.push(target);
  };
  return (
    <Button onClick={onClick} {...buttonProps}>
      {children}
    </Button>
  );
};

export const CenterContent = ({ children }) => (
  <Box display="flex" style={{ width: "100%" }} justifyContent="center">
    <Box>{children}</Box>
  </Box>
);

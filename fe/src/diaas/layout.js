import { Box } from "@material-ui/core";
import React from "react";

export const HCenter = ({ children, ...props }) => (
  <Box display="flex" width="100%" justifyContent="center" {...props}>
    {children}
  </Box>
);

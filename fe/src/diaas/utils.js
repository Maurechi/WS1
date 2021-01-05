import { Box } from "@material-ui/core";

// eslint-disable-next-line
export const ignore = (v) => null;

export const HCenter = ({ children, ...BoxProps }) => (
  <Box display="flex" width="100%" justifyContent="center" {...BoxProps}>
    {children}
  </Box>
);

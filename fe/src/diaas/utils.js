import { Box } from "@material-ui/core";
import _ from "lodash";

// eslint-disable-next-line
export const ignore = (v) => null;

export const HCenter = ({ children, ...BoxProps }) => (
  <Box display="flex" width="100%" justifyContent="center" {...BoxProps}>
    {children}
  </Box>
);

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

export const NotFound = ({ children }) => (
  <Box style={{ width: "100%" }}>
    <HCenter>Not Found</HCenter>
    <Box>{children}</Box>
  </Box>
);

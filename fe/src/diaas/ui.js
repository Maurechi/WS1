import { Box, Button, CircularProgress, Typography } from "@material-ui/core";
import _ from "lodash";
import React, { useEffect, useLayoutEffect, useState } from "react";
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

export const ActionButton = wrapInBox(({ onClick, disabled = null, enabled = null, children, color = "secondary" }) => {
  const [state, setState] = useState("idle");
  const buttonOnClick = () => {
    setState("busy");
    Promise.resolve(onClick()).then((res) => {
      setState("idle");
      return res;
    });
  };
  const isIdle = state === "idle";
  if (enabled !== null && disabled !== null && enabled !== disabled) {
    throw new Error(`Incompatable enabled (${enabled}) and disabled (${disabled}) settings.`);
  }
  if (enabled !== null) {
    disabled = !enabled;
  }
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

export const ContentTitle = ({ iconURL, children }) => (
  <Box pb={2} display="flex" style={{ width: "100%" }}>
    <Box pr={2}>
      <img src={`/i/icons/${iconURL}`} alt={`Icon for page content`} width={20} />
    </Box>
    <Box style={{ flexGrow: 1 }}>{children}</Box>
  </Box>
);

export const NotFound = ({ children }) => (
  <Box style={{ width: "100%" }}>
    <HCenter>Not Found</HCenter>
    <Box>{children}</Box>
  </Box>
);

export const useResize = (ref) => {
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  const updateDimensions = () => {
    if (ref.current) {
      setDimensions({
        width: ref.current.offsetWidth,
        height: ref.current.offsetHeight,
      });
    }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useLayoutEffect(() => updateDimensions(), []);

  useEffect(() => {
    window.addEventListener("resize", updateDimensions);

    return () => {
      window.removeEventListener("resize", updateDimensions);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return dimensions;
};

export const Literal = ({ children }) => <pre style={{ whiteSpace: "pre-wrap" }}>{children}</pre>;

export const DefinitionTable = ({ children }) => {
  return (
    <table>
      <tbody>{children}</tbody>
    </table>
  );
};

DefinitionTable.Term = ({ label, children }) => (
  <tr>
    <td style={{ verticalAlign: "top", whiteSpace: "nowrap" }}>
      <Box px={1}>{label}</Box>
    </td>
    <td style={{ verticalAlign: "top" }}>{children}</td>
  </tr>
);

/// https://material-ui.com/components/progress/
export const CircularProgressWithLabel = ({ children, value }) => {
  return (
    <Box position="relative" display="inline-flex">
      <CircularProgress variant="determinate" value={value} />
      <Box
        top={0}
        left={0}
        bottom={0}
        right={0}
        position="absolute"
        display="flex"
        alignItems="center"
        justifyContent="center"
      >
        <Typography variant="caption" component="div" color="textSecondary">
          {children}
        </Typography>
      </Box>
    </Box>
  );
};

export const useTick = ({ start = 0, bound, step = 1, interval = 1000 }) => {
  const [tick, setTick] = useState(start);
  useEffect(() => {
    let t = start;
    const intervalId = setInterval(() => {
      t = (t + step) % bound;
      setTick(t);
    }, interval);
    return () => {
      clearInterval(intervalId);
    };
  }, [bound, interval, start, step]);
  return tick;
};

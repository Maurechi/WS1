import { Box } from "@material-ui/core";
import React, { useEffect } from "react";

import { useAppState } from "diaas/state.js";

export const AccountProfileContent = () => {
  return <Box>Profile</Box>;
};

export const AccountLogoutContent = () => {
  const state = useAppState();
  useEffect(() => {
    state.logout().then(() => {
      window.location.pathname = "/";
      window.location.reload(true);
    });
  }, [state]);
  return <Box>Logging out.</Box>;
};

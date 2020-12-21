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
      console.log("Updating window location");
      window.location.pathname = "/";
      window.location.reload(true);
    });
  }, [state]);
  return <Box>Loggin out.</Box>;
};

import { Box } from "@material-ui/core";
import { observer } from "mobx-react-lite";
import React, { useEffect } from "react";

import { useAppState } from "diaas/state.js";

export const AccountProfileContent = observer(() => {
  const {
    user: { display_name, uid, email },
  } = useAppState();

  return (
    <Box>
      <p>
        Profile <tt>{email}</tt>
      </p>
      <p>
        Hello {display_name} (<tt>{uid}</tt>)
      </p>
    </Box>
  );
});

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

import { Box } from "@material-ui/core";

import { useAppState } from "diaas/state.js";

export const StoresContent = () => {
  const { user } = useAppState();
  const stores = user.dataStacks[0].stores;
  if (stores.length === 0) {
    return <Box>No Stores.</Box>;
  } else {
    const store = stores[0];
    return <>Store is a {store.type}</>;
  }
};

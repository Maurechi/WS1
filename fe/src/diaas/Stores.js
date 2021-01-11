import { Box } from "@material-ui/core";

import { useAppState } from "diaas/state.js";

export const StoresContent = () => {
  const { user } = useAppState();
  const stores = user.dataStacks[0].stores;
  if (stores.length === 0) {
    return <Box>No Stores.</Box>;
  } else {
    const { id, type, ...config } = stores[0];

    return (
      <>
        <p>
          Store `{id}` is a {type}.
        </p>
        <p>Configuration:</p>
        <pre>{JSON.stringify(config, null, 4)}</pre>
      </>
    );
  }
};

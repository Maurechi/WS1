import { Box } from "@material-ui/core";

import { useAppState } from "diaas/state.js";

export const StoresContent = () => {
  const { user } = useAppState();
  const stores = user.data_stacks[0].stores;
  if (stores.length === 0) {
    return <Box>No Stores.</Box>;
  } else {
    const { id, type, ...config } = stores[0];
    const icon = type === "libds.store.postgresql.PostgreSQL" ? "postgresql.svg" : "404.gif";
    const alt = type === "libds.store.postgresql.PostgreSQL" ? "PostgreSQL DB" : "Unknown Type";

    return (
      <>
        <p>
          <img width="100em" src={`/i/logos/${icon}`} alt={alt} />
        </p>
        <table>
          <tr>
            <td>Id:</td>
            <td>
              <tt>{id}</tt>
            </td>
          </tr>
          <tr>
            <td>Host:</td>
            <td>{config.parameters.host}</td>
          </tr>
          <tr>
            <td>Port:</td>
            <td>{config.parameters.port}</td>
          </tr>
          <tr>
            <td>User:</td>
            <td>{config.parameters.user}</td>
          </tr>
          <tr>
            <td>Parameters:</td>
            <td>
              <pre>{JSON.stringify(config, null, 4)}</pre>
            </td>
          </tr>
        </table>
      </>
    );
  }
};

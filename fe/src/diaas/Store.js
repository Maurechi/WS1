import { Box } from "@material-ui/core";

import { useAppState } from "diaas/state.js";

const StoreIcon = ({ icon, alt }) => (
  <p>
    <img width="100em" src={`/i/icons/${icon}`} alt={alt} />
  </p>
);

const StoreTable = ({ store, children }) => (
  <table>
    <tbody>
      <tr>
        <td>Id:</td>
        <td>
          <tt>{store.id}</tt>
        </td>
      </tr>
      {children}
      <tr>
        <td>Parameters:</td>
        <td>
          <pre>{JSON.stringify(store, null, 4)}</pre>
        </td>
      </tr>
    </tbody>
  </table>
);

const ClickHouse = ({ store }) => {
  return (
    <>
      <StoreIcon icon="clickhouse.png" alt="ClickHouse" />
      <StoreTable store={store}>
        <tr>
          <td>Host:</td>
          <td>{store.parameters.host}</td>
        </tr>
        <tr>
          <td>Port:</td>
          <td>{store.parameters.port}</td>
        </tr>
      </StoreTable>
    </>
  );
};

const SQLite = ({ store }) => {
  return (
    <>
      <StoreIcon icon="sqlite.png" alt="SQLite" />
      <StoreTable store={store}>
        <tr>
          <td>Path:</td>
          <td>{store.parameters.path}</td>
        </tr>
      </StoreTable>
    </>
  );
};

export const StoreContent = () => {
  const { user } = useAppState();
  const store = user.dataStack ? user.dataStack.store : null;
  if (store === null) {
    return <Box>No Store.</Box>;
  } else {
    if (store.type === "libds.store.sqlite.SQLite") {
      return <SQLite store={store} />;
    } else if (store.type === "libds.store.clickhouse.ClickHouse") {
      return <ClickHouse store={store} />;
    } else {
      return (
        <>
          <StoreIcon icon="404.gif" alt="Unknown Type" />
          <StoreTable store={store} />
        </>
      );
    }
  }
};

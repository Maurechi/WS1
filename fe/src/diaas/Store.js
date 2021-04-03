import { Box } from "@material-ui/core";

import { useAppState } from "diaas/state.js";

const StoreLogo = ({ logo, alt }) => (
  <p>
    <img width="100em" src={`/i/logos/${logo}`} alt={alt} />
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

const PostgreSQL = (store) => {
  return (
    <>
      <StoreLogo logo="postgresql.svg" alt="PostgreSQL DB" />
      <StoreTable store={store}>
        <tr>
          <td>Host:</td>
          <td>{store.parameters.host}</td>
        </tr>
        <tr>
          <td>Port:</td>
          <td>{store.parameters.port}</td>
        </tr>
        <tr>
          <td>User:</td>
          <td>{store.parameters.user}</td>
        </tr>
      </StoreTable>
    </>
  );
};

const ClickHouse = ({ store }) => {
  return (
    <>
      <StoreLogo logo="clickhouse.png" alt="ClickHouse" />
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

export const StoreContent = () => {
  const { user } = useAppState();
  const store = user.dataStack ? user.dataStack.store : null;
  if (store === null) {
    return <Box>No Store.</Box>;
  } else {
    if (store.type === "libds.store.postgresql.PostgreSQL") {
      return <PostgreSQL store={store} />;
    } else if (store.type === "libds.store.clickhouse.ClickHouse") {
      return <ClickHouse store={store} />;
    } else {
      return (
        <>
          <StoreLogo logo="404.gif" alt="Unknown Type" />
          <StoreTable store={store} />
        </>
      );
    }
  }
};

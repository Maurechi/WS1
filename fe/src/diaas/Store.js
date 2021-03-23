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

const PostgreSQL = (config) => {
  return (
    <>
      <SourceLogo logo="postgresql.svg" alt="PostgreSQL DB" />
      <SourceTable config={config}>
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
      </SourceTable>
    </>
  );
};

const ClickHouse = ({ config }) => {
  return (
    <>
      <SourceLogo logo="clickhouse.png" alt="ClickHouse" />
      <SourceTable config={config}>
        <tr>
          <td>Host:</td>
          <td>{config.parameters.host}</td>
        </tr>
        <tr>
          <td>Port:</td>
          <td>{config.parameters.port}</td>
        </tr>
      </SourceTable>
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
      return <PostgreSQL config={config} />;
    } else if (store.type === "libds.store.clickhouse.ClickHouse") {
      return <ClickHouse config={config} />;
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

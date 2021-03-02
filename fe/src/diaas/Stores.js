import { Box } from "@material-ui/core";

import { useAppState } from "diaas/state.js";

const SourceLogo = ({ logo, alt }) => (
  <p>
    <img width="100em" src={`/i/logos/${logo}`} alt={alt} />
  </p>
);

const SourceTable = ({ config, children }) => (
  <table>
    <tbody>
      <tr>
        <td>Id:</td>
        <td>
          <tt>{config.id}</tt>
        </td>
      </tr>
      {children}
      <tr>
        <td>Parameters:</td>
        <td>
          <pre>{JSON.stringify(config, null, 4)}</pre>
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

export const StoresContent = () => {
  const { user } = useAppState();
  const stores = user.dataStack ? user.dataStack.stores : [];
  if (stores.length === 0) {
    return <Box>No Stores.</Box>;
  } else {
    const config = stores[0];
    if (config.type === "libds.store.postgresql.PostgreSQL") {
      return <PostgreSQL config={config} />;
    } else if (config.type === "libds.store.clickhouse.ClickHouse") {
      return <ClickHouse config={config} />;
    } else {
      return (
        <>
          <SourceLogo logo="404.gif" alt="Unknown Type" />
          <SourceTable config={config} />
        </>
      );
    }
  }
};

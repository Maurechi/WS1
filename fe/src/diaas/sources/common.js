import _ from "lodash";
import { useHistory } from "react-router-dom";

import { useAppState } from "diaas/state.js";

export const useSourceFileUpdater = () => {
  const { user, backend } = useAppState();
  const history = useHistory();
  return ({ src_id, dst_id, data }) => {
    const src = `sources/${src_id}.yaml`;
    const dst = `sources/${dst_id}.yaml`;

    return backend
      .postFile(src, data)
      .then(() => {
        if (src !== dst) {
          return backend.moveFile(src, dst);
        } else {
          return Promise.resolve(null);
        }
      })
      .then(() => {
        return backend.sourceInfo(dst_id);
      })
      .then((source) => {
        let sources = user.data_stacks[0].sources;
        sources = _.filter(sources, (s) => s.id !== src_id);
        sources.push(source);
        source = _.sortBy(sources, "id");
        user.data_stacks[0].sources = sources;
        return history.replace(`/sources/${dst_id}`);
      });
  };
};

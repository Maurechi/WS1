import { MenuItem } from "@material-ui/core";
import _ from "lodash";
import { useHistory } from "react-router-dom";

import { Select, TextField, useFormValue } from "diaas/form.js";
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

export const IntervalSelector = ({ value }) => {
  const displayValue = useFormValue(value.v || "@never", {
    serialize: (v) => {
      value.v = v === "@never" ? null : v;
      return value.v;
    },
    parse: () => value.v || "@never",
  });
  if (_.includes(["@never", "3600s", "12600s", "43200s", "86400s"], displayValue.v)) {
    return (
      <Select value={displayValue} fullWidth={true}>
        <MenuItem value="@never">Manual Refresh Only</MenuItem>
        <MenuItem value="3600s">1 Hour</MenuItem>
        <MenuItem value="12600s">6 Hours</MenuItem>
        <MenuItem value="43200s">12 Hours</MenuItem>
        <MenuItem value="86400s">24 Hours</MenuItem>
      </Select>
    );
  } else {
    return <TextField value={value} disabled={true} />;
  }
};

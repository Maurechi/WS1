import { Dialog, DialogContent, DialogContentText, DialogTitle } from "@material-ui/core";
import React from "react";
import { HCenter} from "diaas/utils.js";

import image from "./Error.gif";

export const ErrorDialog = ({ title, message }) => {
  return (
    <Dialog open={true} aria-labelledby="alert-dialog-title" aria-describedby="alert-dialog-description">
      <DialogTitle id="alert-dialog-title">{title}</DialogTitle>
      <DialogContent>
        <HCenter>
          <img src={image} alt="broken bridge gif" width="482px" />
        </HCenter>
        <DialogContentText id="alert-dialog-description">{message}</DialogContentText>
      </DialogContent>
    </Dialog>
  );
};

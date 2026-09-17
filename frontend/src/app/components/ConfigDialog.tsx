

"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { StandaloneConfig } from "@/lib/config";

interface ConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (config: StandaloneConfig) => void;
  initialConfig?: StandaloneConfig;
}

export function ConfigDialog({
  open,
  onOpenChange,
  onSave,
  initialConfig,
}: ConfigDialogProps) {
  const [deploymentUrl, setDeploymentUrl] = useState(
    initialConfig?.deploymentUrl || ""
  );
  const [assistantId, setAssistantId] = useState(
    initialConfig?.assistantId || ""
  );
  const [langsmithApiKey, setLangsmithApiKey] = useState(
    initialConfig?.langsmithApiKey || ""
  );

  useEffect(() => {
    if (open && initialConfig) {
      setDeploymentUrl(initialConfig.deploymentUrl);
      setAssistantId(initialConfig.assistantId);
      setLangsmithApiKey(initialConfig.langsmithApiKey || "");
    }
  }, [open, initialConfig]);

  const handleSave = () => {
    if (!deploymentUrl || !assistantId) {
      alert("Please fill  required fields");
      return;
    }

    onSave({
      deploymentUrl,
      assistantId,
      langsmithApiKey: langsmithApiKey || undefined,
    });
    onOpenChange(false);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle className="bg-gradient-to-r from-sky-400 via-blue-500 to-indigo-600 bg-clip-text text-transparent drop-shadow-[0_0_12px_rgba(59,130,246,0.6)] hover:drop-shadow-[0_0_20px_rgba(59,130,246,0.8)] transition-all duration-300">Configuration</DialogTitle>
          <DialogDescription>
            Configure your assistant deployment settings.
            These settings will be saved in your browser's local storage.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            {/*<Label htmlFor="deploymentUrl">AI Worker URL</Label>*/}
            <Label htmlFor="assistantId" className="bg-gradient-to-r from-sky-400 via-blue-500 to-indigo-600 bg-clip-text text-transparent font-semibold drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]">AI Worker URL：</Label>

            <Input
              id="deploymentUrl"
              placeholder="https://<deployment address>"
              value={deploymentUrl}
              onChange={(e) => setDeploymentUrl(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="assistantId" className="bg-gradient-to-r from-sky-400 via-blue-500 to-indigo-600 bg-clip-text text-transparent font-semibold drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]">AI Worker ID：</Label>
            <Input
              id="assistantId"
              placeholder="<Agent ID defined in agentConfig.yaml>"
              value={assistantId}
              onChange={(e) => setAssistantId(e.target.value)}
            />
          </div>
          {/*<div className="grid gap-2">*/}
          {/*  <Label htmlFor="langsmithApiKey">*/}
          {/*    LangSmith API Key{" "}*/}
          {/*    <span className="text-muted-foreground">(Optional)</span>*/}
          {/*  </Label>*/}
          {/*  <Input*/}
          {/*    id="langsmithApiKey"*/}
          {/*    type="password"*/}
          {/*    placeholder="lsv2_pt_..."*/}
          {/*    value={langsmithApiKey}*/}
          {/*    onChange={(e) => setLangsmithApiKey(e.target.value)}*/}
          {/*  />*/}
          {/*</div>*/}
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="bg-gradient-to-r from-gray-300 via-gray-400 to-gray-500 text-white border-0 shadow-[0_0_15px_rgba(107,114,128,0.4)] hover:shadow-[0_0_25px_rgba(107,114,128,0.6)] hover:from-gray-400 hover:via-gray-500 hover:to-gray-600 transition-all duration-300"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            className="bg-gradient-to-r from-green-400 via-green-500 to-emerald-600 text-white shadow-[0_0_20px_rgba(34,197,94,0.5)] hover:shadow-[0_0_30px_rgba(34,197,94,0.7)] hover:from-green-500 hover:via-green-600 hover:to-emerald-700 border-0 transition-all duration-300"
          >
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
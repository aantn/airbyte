import React, { useContext, useMemo, useState } from "react";
import { useSet } from "react-use";
import { setIn } from "formik";

import { AirbyteStreamConfiguration, SyncSchemaStream } from "core/domain/catalog";

const Context = React.createContext<BatchContext | null>(null);

interface BatchContext {
  isActive: boolean;
  toggleNode: (id: string) => void;
  onCheckAll: () => void;
  allChecked: boolean;
  selectedBatchNodes: SyncSchemaStream[];
  selectedBatchNodeIds: string[];
  onChangeOption: (
    value:
      | ((prevState: Partial<AirbyteStreamConfiguration>) => Partial<AirbyteStreamConfiguration>)
      | Partial<AirbyteStreamConfiguration>
  ) => void;
  options: Partial<AirbyteStreamConfiguration>;
  onApply: () => void;
  onCancel: () => void;
}

const defaultOptions: Partial<AirbyteStreamConfiguration> = {
  selected: false,
};

const BatchEditProvider: React.FC<{
  nodes: SyncSchemaStream[];
  update: (streams: SyncSchemaStream[]) => void;
}> = ({ children, nodes, update }) => {
  const [selectedBatchNodes, { reset, toggle, add }] = useSet<string>(new Set());
  const [options, setOptions] = useState<Partial<AirbyteStreamConfiguration>>(defaultOptions);

  const resetBulk = () => {
    reset();
    setOptions(defaultOptions);
  };

  const onApply = () => {
    const updatedConfig = nodes.map((node) =>
      selectedBatchNodes.has(node.id) ? setIn(node, "config", { ...node.config, ...options }) : node
    );

    update(updatedConfig);
    resetBulk();
  };

  const onCancel = () => {
    reset();
    resetBulk();
  };

  const isActive = selectedBatchNodes.size > 0;
  const allChecked = selectedBatchNodes.size === nodes.length;

  const ctx: BatchContext = {
    isActive: isActive,
    toggleNode: toggle,
    onCheckAll: () => (allChecked ? reset() : nodes.forEach((n) => add(n.id))),
    allChecked: allChecked,
    selectedBatchNodeIds: Array.from(selectedBatchNodes),
    selectedBatchNodes: nodes.filter((n) => selectedBatchNodes.has(n.id)),
    onChangeOption: (newOptions) => setOptions({ ...options, ...newOptions }),
    options,
    onApply,
    onCancel,
  };

  return <Context.Provider value={ctx}>{children}</Context.Provider>;
};

const useBulkEdit = (): BatchContext => {
  const ctx = useContext(Context);

  if (!ctx) {
    throw new Error("useBulkEdit should be used within BatchEditProvider");
  }

  return ctx;
};

const useBulkEditSelect = (id: string): [boolean, () => void] => {
  const { selectedBatchNodeIds, toggleNode } = useBulkEdit();
  const isIncluded = selectedBatchNodeIds.includes(id);

  return useMemo(() => [isIncluded, () => toggleNode(id)], [isIncluded, toggleNode, id]);
};

export type { BatchContext };
export { useBulkEditSelect, useBulkEdit, BatchEditProvider };

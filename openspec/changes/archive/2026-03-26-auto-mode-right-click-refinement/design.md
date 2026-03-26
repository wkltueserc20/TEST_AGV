## Context

目前 `App.tsx` 中的 `onCanvasRightClick` 函式處理 `AUTO` 模式時，其行為由 `perm === 'CANCEL_TASK'` 觸發。目前的實作僅重置了 `autoTaskSource` 狀態，這會停止任務指派流程，但不會取消側邊欄已選中的物件或車輛。

## Goals / Non-Goals

**Goals:**
- 在 `AUTO` 模式下右鍵點擊時，一併清空 `selectedAgvId` 和 `selectedObId`。

**Non-Goals:**
- 不改變 `MODE_PERMISSIONS` 的結構。
- 不影響其他模式的右鍵行為（如 `SINGLE_ACTION` 或 `SELECT`）。

## Decisions

### 1. 修改 `onCanvasRightClick` 分流邏輯
在 `App.tsx` 中，找到 `onCanvasRightClick` 的定義處。針對 `perm === 'CANCEL_TASK'` 區塊，擴展其執行的狀態變更：

```typescript
// 變更前
} else if (perm === 'CANCEL_TASK') {
    setAutoTaskSource(null);
}

// 變更後
} else if (perm === 'CANCEL_TASK') {
    setAutoTaskSource(null);
    setSelectedAgvId(null);
    setSelectedObId(null);
}
```

## Risks / Trade-offs

- **[Risk] 使用者誤觸**：使用者可能只想取消任務起點而不想取消選中對象。
  - **Mitigation**: 考量到 `AUTO` 模式通常是完整的任務流程，一鍵重置符合大多數工業軟體的「取消」直覺（Escape 行為）。

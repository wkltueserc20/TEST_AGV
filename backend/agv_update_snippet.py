    def update(self, dt: float, world):
        # 1. 狀態速度鎖定：裝卸料、等待中、思考中或受困時，強制禁止移動並立即回傳
        if self.status in [AGVStatus.LOADING, AGVStatus.UNLOADING, AGVStatus.WAITING, AGVStatus.THINKING, AGVStatus.STUCK]:
            self.v = 0; self.omega = 0; self.target_v = 0; self.target_omega = 0
            self.l_rpm, self.r_rpm = 0, 0
            
            # --- Traffic Control: WAITING 狀態下的任務恢復偵測 ---
            if self.status == AGVStatus.WAITING:
                # 修正：如果完全沒有任務，則不應待在 WAITING，直接轉為 IDLE
                if not self.current_task:
                    logger.info(f"AGV {self.id} has no task. Resetting from WAITING to IDLE.")
                    self.status = AGVStatus.IDLE
                    self.is_running = False
                    self.yielding_to_id = None
                    self.original_target = None
                    return

                if self.yielding_to_id:
                    # 強制至少等待 15 秒再重新規劃，避免震盪
                    if self.wait_start_time and (time.time() - self.wait_start_time > 15.0):
                        if self.original_target:
                            other_path = world.path_occupancy.get(self.yielding_to_id, [])
                            conflict_cleared = True
                            if other_path:
                                for ox, oy in other_path[:100]:
                                    if (ox - self.x)**2 + (oy - self.y)**2 < 6250000: # 2.5m
                                        conflict_cleared = False; break
                            
                            if conflict_cleared:
                                logger.info(f"AGV {self.id} conflict with {self.yielding_to_id} cleared. Resuming task.")
                                self.target = self.original_target
                                self.original_target = None
                                self.yielding_to_id = None
                                self.is_running = True
                                self.replan_needed = True
                                self.status = AGVStatus.PLANNING
                                return # 立即回傳，讓下一幀啟動規劃

            # 裝卸料計時處理
            if self.status in [AGVStatus.LOADING, AGVStatus.UNLOADING]:

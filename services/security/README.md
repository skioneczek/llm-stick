# Security Interfaces
- unlock_with_pin(pin:str)->bool
- change_pin(current:str,new:str)->bool
- reset_with_recovery(words:list[str])->bool
- failed_attempt(count:int)->LockoutState
- wipe_temps()->None
- clear_logs()->None

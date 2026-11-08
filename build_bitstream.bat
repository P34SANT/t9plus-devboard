@echo off
setlocal enabledelayedexpansion

REM ==========================================================================
REM  build_bitstream.bat - One-Click Bitstream Builder for Antminer T9+
REM ==========================================================================

echo ==========================================================================
echo  Antminer T9+ Devboard: One-Click Vivado Bitstream Builder
echo ==========================================================================

REM Locate Vivado
set VIVADO_BAT=C:\AMDDesignTools\2026.1\Vivado\bin\vivado.bat
if not exist "%VIVADO_BAT%" (
    if defined XILINX_VIVADO (
        set VIVADO_BAT=%XILINX_VIVADO%\bin\vivado.bat
    )
)

if not exist "%VIVADO_BAT%" (
    echo [ERROR] Vivado executable not found at:
    echo   %VIVADO_BAT%
    echo Please ensure AMD Vitis/Vivado is installed or set XILINX_VIVADO.
    pause
    exit /b 1
)

echo [*] Found Vivado: %VIVADO_BAT%
echo [*] Starting synthesis and implementation in batch mode...
echo [*] Log will be written to vivado_build.log
echo.

call "%VIVADO_BAT%" -mode batch -source vivado\build_bitstream.tcl -log vivado_build.log -journal vivado_build.jou

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed! Check vivado_build.log for details.
    pause
    exit /b %ERRORLEVEL%
)

if exist "t9_base.bit" (
    echo.
    echo ==========================================================================
    echo  SUCCESS: t9_base.bit successfully generated!
    echo ==========================================================================
    echo.
    set /p UPLOAD="Upload and program to board at 192.168.2.99 now? (Y/N): "
    if /i "!UPLOAD!"=="Y" (
        echo [*] Uploading t9_base.bit via SCP...
        scp t9_base.bit xilinx@192.168.2.99:/home/xilinx/
        if !ERRORLEVEL! EQU 0 (
            echo [*] Programming FPGA via Linux fpga_manager...
            ssh xilinx@192.168.2.99 "sudo load_bit /home/xilinx/t9_base.bit"
            echo [+] Done! D1 Green LED should now be lit.
        ) else (
            echo [-] Could not connect to board at 192.168.2.99.
        )
    )
) else (
    echo [ERROR] Expected output t9_base.bit was not found.
)

pause

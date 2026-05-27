# E-Ink Bus Picture Frame

Forked from Lionel Tan's repository 

## Things you will need
1. Raspberry Pi Zero W with 40-pin GPIO headers
2. Waveshare 7.5inch E-Ink Display (EPD 7in5 V2) - make sure you get the one with the HAT to connect to the Pi
3. IKEA 7x5 picture frame
4. 5V 3A power supply
5. Micro USB flat cable
6. 4GB or more SD card


## Create a .env file in /app
   ```
   API_KEY=your_lta_api_key //Get this from LTA DataMall
   BUS_STOP_CODE_A=your_first_bus_stop_code
   BUS_STOP_CODE_B=your_second_bus_stop_code
   ALLOWED_TELEGRAM_ID=<your telegram user id>
   BOT_TOKEN=<create your own Telegram bot to control messages>
   ```

## How to run script automatically on Raspberry Pi  

1. **Create a systemd service file**:
   - Open a terminal.
   - Use a text editor like `nano` to create a new service file:

     ```bash
     sudo nano /etc/systemd/system/bus_display.service
     ```

2. **Add the following content to the service file**:

    ```ini
    [Unit]
    Description=E-Ink Bus Display Service
    After=multi-user.target

    [Service]
    ExecStart=/usr/bin/python3 /path/to/your/app/main.py
    WorkingDirectory=/path/to/your/
    StandardOutput=inherit
    StandardError=inherit
    Restart=always
    User=pi

    [Install]
    WantedBy=multi-user.target
    ```

    - **ExecStart**: Replace `/path/to/your/script.py` with the full path to your Python script.
    - **WorkingDirectory**: Replace `/path/to/your/` with the directory containing your script.
    - **User**: Replace `pi` with the username under which the script should run, if different.
    - `Restart=always` ensures that the service restarts if it fails.

3. **Save and exit**:
   - Press `Ctrl + X`, then `Y`, and then `Enter` to save and exit `nano`.

### Step 2: Enable the Service

1. **Reload systemd to recognize the new service**:

    ```bash
    sudo systemctl daemon-reload
    ```

2. **Enable the service to start on boot**:

    ```bash
    sudo systemctl enable bus_display.service
    ```

3. **Start the service immediately (optional)**:

    ```bash
    sudo systemctl start bus_display.service
    ```

4. **Check the status of the service**:

    ```bash
    sudo systemctl status bus_display.service
    ```

    This command will show whether the service is active and running.


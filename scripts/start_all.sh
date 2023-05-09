source ~/.env
~/iot/Drivers/kickr_climb_and_smart_trainer/incline_and_resistance_control.py --mac_address ${KICKR_MAC_ADDRESS} --broker_address ${MQTT_HOSTNAME} --username ${MQTT_USERNAME} --password ${MQTT_PASSWORD} --resistance_command_topic bike/${DEVICE_ID}/resistance/control --resistance_report_topic bike/${DEVICE_ID}/resistance --incline_command_topic bike/${DEVICE_ID}/incline/control --incline_report_topic bike/${DEVICE_ID}/incline --speed_report_topic bike/${DEVICE_ID}/speed --cadence_report_topic bike/${DEVICE_ID}/cadence --power_report_topic bike/${DEVICE_ID}/power &
~/iot/Drivers/fan/fan.py &
~/iot/Drivers/heart_rate_sensor/heartrate.py &
cd ~/iot/Drivers/workout
npm run start

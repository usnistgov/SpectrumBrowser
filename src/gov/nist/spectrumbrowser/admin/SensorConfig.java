package gov.nist.spectrumbrowser.admin;

import java.util.ArrayList;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserWidget;
import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

public class SensorConfig extends AbstractSpectrumBrowserWidget implements
		SpectrumBrowserScreen, SpectrumBrowserCallback<String> {

	private Admin admin;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private Grid grid;
	private boolean updateFlag;

	ArrayList<Sensor> sensors = new ArrayList<Sensor>();
	private HorizontalPanel titlePanel;

	class ThresholdButtonHandler implements ClickHandler {
		private Sensor sensor;

		ThresholdButtonHandler(Sensor sensor) {
			this.sensor = sensor;
		}

		@Override
		public void onClick(ClickEvent event) {
			new SweptFrequencySensorBands(admin, SensorConfig.this, sensor,
					verticalPanel).draw();
		}
	}

	public SensorConfig(Admin admin) {
		try {
			this.admin = admin;
			updateFlag = true;
			Admin.getAdminService().getSensorInfo(true, this);
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Problem contacting host", th);
			Window.alert("Problem communicating with server");
			admin.logoff();

		}

	}

	public void setUpdateFlag(boolean flag) {
		this.updateFlag = flag;
	}

	private void repopulate(JSONArray sensorArray) {
		sensors.clear();
		for (int i = 0; i < sensorArray.size(); i++) {
			JSONObject sensorObj = sensorArray.get(i).isObject();
			Sensor sensor = new Sensor(sensorObj);
			sensors.add(sensor);
		}
	}

	public void redraw() {
		try {
			updateFlag = true;
			this.sensors.clear();
			Admin.getAdminService().getSensorInfo(true,this);
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Problem contacting host", th);
			Window.alert("Problem communicating with server");
			admin.logoff();
		}
	}

	@Override
	public void onSuccess(String result) {
		JSONObject jsonObject = JSONParser.parseLenient(result).isObject();
		String flag = jsonObject.get("status").isString().stringValue();
		logger.finer(result);
		if (flag.equals("OK")) {
			JSONArray sensorArray = jsonObject.get("sensors").isArray();
			repopulate(sensorArray);
			if (updateFlag) {
				draw();
				updateFlag = false;
			}
		} else {
			String errorMessage = jsonObject.get("ErrorMessage").isString()
					.stringValue();
			Window.alert(errorMessage);
			draw();
		}
	}

	@Override
	public void onFailure(Throwable throwable) {
		Window.alert("Error communicating with the server");
		admin.logoff();
	}

	@Override
	public void draw() {
		verticalPanel.clear();
		
		HTML title = new HTML("<h3>Configured sensors. </h3>");
		

		titlePanel = new HorizontalPanel();
		titlePanel.add(title);
		HTML subtitle = new HTML("<p>Select Add button to add a new sensor. "
				+ "Buttons on each sensor row allow you to reconfigure the sensor.</p>");
		verticalPanel.add(titlePanel);
		verticalPanel.add(subtitle);;
		grid = new Grid(sensors.size() + 1, 15);

		for (int i = 0; i < grid.getColumnCount(); i++) {
			grid.getCellFormatter().setStyleName(0, i, "textLabelStyle");
		}

		for (int i = 0; i < grid.getRowCount(); i++) {
			for (int j = 0; j < grid.getColumnCount(); j++) {
				grid.getCellFormatter().setHorizontalAlignment(i, j,
						HasHorizontalAlignment.ALIGN_CENTER);
				grid.getCellFormatter().setVerticalAlignment(i, j,
						HasVerticalAlignment.ALIGN_MIDDLE);
			}
		}
		grid.setCellPadding(2);
		grid.setCellSpacing(2);
		grid.setBorderWidth(2);

		int col = 0;

		// Column headings.
		grid.setText(0, col++, "Sensor ID");
		grid.setText(0, col++, "Sensor Key");
		grid.setText(0, col++, "Measurement Type");
		grid.setText(0, col++, "Sensor Admin Email");
		grid.setText(0, col++, "Data Retention (months)");
		grid.setText(0, col++, "Garbage Collect");
		grid.setText(0, col++, "Frequency Bands");
		grid.setText(0, col++, "Recompute Message Occupancies");
		grid.setText(0, col++, "Show Message Dates");
		grid.setText(0, col++, "Enabled?");
		grid.setText(0, col++, "Get System Messages");
		grid.setText(0, col++, "Streaming Port");
		grid.setText(0, col++, "Startup Params");
		grid.setText(0, col++, "Duplicate Row");
		grid.setText(0, col++, "Purge");

		int row = 1;
		for (final Sensor sensor : sensors) {

			col = 0;

			grid.setText(row, col++, sensor.getSensorId()); // 0
			final TextBox sensorKeyTextBox = new TextBox();

			grid.setWidget(row, col++, sensorKeyTextBox);
			sensorKeyTextBox.setText(sensor.getSensorKey());
			sensorKeyTextBox.setWidth("120px");
			sensorKeyTextBox
					.addValueChangeHandler(new ValueChangeHandler<String>() {

						@Override
						public void onValueChange(ValueChangeEvent<String> event) {
							String newKey = event.getValue();
							if (!sensor.setSensorKey(newKey)) {
								Window.alert("Please enter a key at least 4 characters long");
								sensorKeyTextBox.setText(sensor.getSensorKey());
								return;
							}
							Admin.getAdminService().updateSensor(
									sensor.toString(), SensorConfig.this);
						}
					});

			grid.setText(row, col++, sensor.getMeasurementType());

			final TextBox adminEmailTextBox = new TextBox();
			adminEmailTextBox.setText(sensor.getSensorAdminEmail());
			adminEmailTextBox
					.addValueChangeHandler(new ValueChangeHandler<String>() {

						@Override
						public void onValueChange(ValueChangeEvent<String> event) {
							String email = event.getValue();
							if (email
									.matches("^[_A-Za-z0-9-]+(\\.[_A-Za-z0-9-]+)*@[A-Za-z0-9-]+(\\.[A-Za-z0-9-]+)*(\\.[A-Za-z]{2,})$")) {
								sensor.setSensorAdminEmail(email);
							} else {
								Window.alert("please enter a valid email address");
								adminEmailTextBox.setText(sensor
										.getSensorAdminEmail());
							}
							Admin.getAdminService().updateSensor(
									sensor.toString(), SensorConfig.this);
						}
					});
			grid.setWidget(row, col++, adminEmailTextBox);

			final TextBox dataRetentionTextBox = new TextBox();
			dataRetentionTextBox.setWidth("30px");
			dataRetentionTextBox.setValue(Integer.toString(sensor
					.getDataRetentionDurationMonths()));
			dataRetentionTextBox
					.addValueChangeHandler(new ValueChangeHandler<String>() {
						@Override
						public void onValueChange(ValueChangeEvent<String> event) {
							try {
								int newRetention = Integer.parseInt(event
										.getValue());
								if (!sensor
										.setDataRetentionDurationMonths(newRetention)) {
									Window.alert("Please enter a valid integer >= 1");
									dataRetentionTextBox.setText(Integer.toString(sensor
											.getDataRetentionDurationMonths()));
									return;
								}
								Admin.getAdminService().updateSensor(
										sensor.toString(), SensorConfig.this);
							} catch (Exception ex) {
								Window.alert("Please enter a valid integer >= 1");
							}
						}
					});
			grid.setWidget(row, col++, dataRetentionTextBox);

			Button cleanupButton = new Button("CleanUp");
			cleanupButton.setTitle("Removes timed out data");
			cleanupButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {

					if (sensor.getSensorStatus().equals("ENABLED")) {
						Window.alert("Please toggle sensor status");
						return;
					}
					boolean yes = Window
							.confirm("Please ensure there are no active user sessions. Deleted records can't be reclaimed.");

					if (yes) {
						titlePanel.clear();
						HTML html = new HTML(
								"<h3>Removing timed out data records. Please wait. This can take a while. </h3>");
						titlePanel.add(html);
						SensorConfig.this.updateFlag = true;
						Admin.getAdminService().garbageCollect(
								sensor.getSensorId(), SensorConfig.this);
					}
				}
			});

			grid.setWidget(row, col++, cleanupButton);

			int thresholdCount = sensor.getThresholds().keySet().size();
			Button thresholdButton;
			if (thresholdCount == 0)
				thresholdButton = new Button("Add");
			else
				thresholdButton = new Button("Change/Add");
			thresholdButton.setTitle("Define Band Occupancy Threshold.");
			if (thresholdCount == 0) {
				thresholdButton.setStyleName("dangerous");
			}
			thresholdButton.addClickHandler(new ClickHandler() {
				@Override
				public void onClick(ClickEvent event) {
					if (sensor.getMeasurementType().equals(Defines.SWEPT_FREQUENCY)) {
						new SweptFrequencySensorBands(admin, SensorConfig.this, sensor,
							verticalPanel).draw();
					} else {
						new FftPowerSensorBands(admin, SensorConfig.this, sensor,
								verticalPanel).draw();
					}
				}
			});

			grid.setWidget(row, col++, thresholdButton);

			Button recomputeButton = new Button("Recompute");
			recomputeButton
					.setTitle("Recomputes per message summary occupancies.");
			recomputeButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					boolean yes = Window
							.confirm("Ensure no users are using the system. This can take a long time. Proceed?");
					if (yes) {
						titlePanel.clear();
						HTML html = new HTML(
								"<h3>Recomputing thresholds - this can take a while. Please wait. </h3>");
						titlePanel.add(html);
						SensorConfig.this.updateFlag = true;
						Admin.getAdminService().recomputeOccupancies(
								sensor.getSensorId(), SensorConfig.this);
					}
				}
			});
			grid.setWidget(row, col++, recomputeButton);

			Button getMessageDates = new Button("Show");
			getMessageDates.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					new ShowMessageDates(admin, SensorConfig.this, sensor,
							verticalPanel).draw();
				}
			});
			grid.setWidget(row, col++, getMessageDates);

			CheckBox statusCheckBox = new CheckBox();
			statusCheckBox.setValue(sensor.getSensorStatus().equals("ENABLED"));
			statusCheckBox
					.addValueChangeHandler(new ValueChangeHandler<Boolean>() {

						@Override
						public void onValueChange(
								ValueChangeEvent<Boolean> event) {
							SensorConfig.this.updateFlag = true;
							Admin.getAdminService().toggleSensorStatus(
									sensor.getSensorId(), SensorConfig.this);

						}
					});

			grid.setWidget(row, col++, statusCheckBox);

			Button downloadSysMessages = new Button("Get");
			grid.setWidget(row, col++, downloadSysMessages);
			downloadSysMessages.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					Admin.getAdminService().getSystemMessages(
							sensor.getSensorId(),
							new SpectrumBrowserCallback<String>() {

								@Override
								public void onSuccess(String result) {
									JSONObject jsonObj = JSONParser
											.parseLenient(result).isObject();
									String status = jsonObj.get("status")
											.isString().stringValue();
									if (status.equals("OK")) {
										Window.alert("Please check your email in 10 minutes for notification");
									} else {
										Window.alert(jsonObj
												.get("ErrorMessage").isString()
												.stringValue());
									}

								}

								@Override
								public void onFailure(Throwable throwable) {
									// TODO Auto-generated method stub

								}
							});
				}
			});

			Button streamingButton =  new Button(
					"Set/Change") ;
			
			if (!sensor.isStreamingEnabled()) {
				streamingButton.setEnabled(false);
				streamingButton.setTitle("Sensor does not support streaming");
			} else {
				streamingButton.setTitle("Configure Streaming");
			}

			
			grid.setWidget(row, col++, streamingButton); // 9
			streamingButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {	
					new SetStreamingParams(admin, verticalPanel, sensor,
								SensorConfig.this).draw();
				}
			});

			TextBox startupParamsTextBox = new TextBox();
			startupParamsTextBox.setWidth("120px");
			grid.setWidget(row, col++, startupParamsTextBox);
			startupParamsTextBox.setTitle("Startup parameters (read by sensor on startup)");
			startupParamsTextBox.setText(sensor.getStartupParams());
			startupParamsTextBox.addValueChangeHandler(new ValueChangeHandler<String> () {

				@Override
				public void onValueChange(ValueChangeEvent<String> event) {
					 sensor.setStartupParams(event.getValue());
					 Admin.getAdminService().updateSensor(
								sensor.toString(), SensorConfig.this);
				}});

			Button dupButton = new Button("Dup");
			dupButton.setTitle("Creates a new sensor with the same settings");
			dupButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					new AddNewSensor(admin, verticalPanel, sensor,
							SensorConfig.this).draw();
				}
			});
			grid.setWidget(row, col++, dupButton);

			Button purgeButton = new Button("Purge");
			purgeButton
					.setTitle("WARNING: Removes Sensor and all data associated with it");
			purgeButton.setStyleName("dangerous");
			purgeButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					if (sensor.getSensorStatus().equals("ENABLED")) {
						Window.alert("Please toggle state of sensor");
						return;
					}
					boolean yes = Window
							.confirm("Remove the sensor and all associated data? Cannot be undone! Ensure no active sessions.");
					if (yes) {
						titlePanel.clear();
						HTML html = new HTML("<h3>Purging sensor "
								+ sensor.getSensorId()
								+ ". This can take a while! </h3>");
						titlePanel.add(html);
						SensorConfig.this.updateFlag = true;
						Admin.getAdminService().purgeSensor(
								sensor.getSensorId(), SensorConfig.this);

					}
				}
			});
			grid.setWidget(row, col++, purgeButton);

			row++;

		}
		verticalPanel.add(grid);
		HorizontalPanel buttonPanel = new HorizontalPanel();
		Button addNewSensorButton = new Button("Add new sensor");
		addNewSensorButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				new AddNewSensor(admin, verticalPanel, SensorConfig.this)
						.draw();
			}
		});
		buttonPanel.add(addNewSensorButton);
		Button refreshButton = new Button("Refresh");
		refreshButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				SensorConfig.this.redraw();
			}
		});
		buttonPanel.add(refreshButton);

		Button logoffButton = new Button("Log Off");
		logoffButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}
		});
		buttonPanel.add(logoffButton);
		verticalPanel.add(buttonPanel);

	}

	@Override
	public String getLabel() {
		return null;
	}

	@Override
	public String getEndLabel() {
		return "Sensors";
	}

	public ArrayList<Sensor> getSensors() {
		return sensors;
	}

}

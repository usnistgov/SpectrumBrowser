package gov.nist.spectrumbrowser.admin;

import java.util.ArrayList;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.Scheduler.ScheduledCommand;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.safehtml.shared.SafeHtml;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.MenuItem;
import com.google.gwt.user.client.ui.TextArea;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserWidget;
import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

public class AddNewSensor  {

	private SensorConfig sensorConfig;
	private Sensor sensor;
	private Admin admin;
	private VerticalPanel verticalPanel;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
    final static boolean passwordCheckingEnabled = false;

	public AddNewSensor(Admin admin, VerticalPanel verticalPanel, SensorConfig sensorConfig) {
		this.sensorConfig = sensorConfig;
		this.sensor = new Sensor();
		this.admin = admin;
		this.verticalPanel = verticalPanel;
	}
	
	public AddNewSensor(Admin admin, VerticalPanel verticalPanel, Sensor existingSensor, SensorConfig sensorConfig){
		this.sensor = Sensor.createNew(existingSensor);
		this.admin = admin;
		this.verticalPanel = verticalPanel;
		this.sensorConfig = sensorConfig;
	}

	public void draw() {
		try {
			logger.finer("AddNewSensor: draw()");
			HTML html = new HTML("<h2>Add New Sensor</h2>");
			verticalPanel.clear();
			verticalPanel.add(html);
			Grid grid = new Grid(5, 2);
			grid.setCellPadding(2);
			grid.setCellSpacing(2);
			grid.setBorderWidth(2);
			int row = 0;
			grid.setText(row, 0, "Sensor ID");
			final TextBox sensorIdTextBox = new TextBox();
			sensorIdTextBox.setText(sensor.getSensorId());
			sensorIdTextBox
					.addValueChangeHandler(new ValueChangeHandler<String>() {

						@Override
						public void onValueChange(ValueChangeEvent<String> event) {
							String sensorId = event.getValue();
							
							if (sensorId == null || sensorId.equals("")
									|| sensorId.equals("UNKNOWN")) {
								Window.alert("Please enter a valid sensor ID");
								return;
							}
							ArrayList<Sensor> sensors = sensorConfig.getSensors();
							for (Sensor sensor : sensors) {
								if (sensorId.equals(sensor.getSensorId())) {
									Window.alert("Please enter a unique sensor ID");
									return;
								}
							}
							sensor.setSensorId(sensorId);

						}
					});
			grid.setWidget(row, 1, sensorIdTextBox);

			row++;
			grid.setText(row, 0, "Sensor Key");
			final TextBox sensorKeyTextBox = new TextBox();

			sensorKeyTextBox
					.addValueChangeHandler(new ValueChangeHandler<String>() {

						@Override
						public void onValueChange(ValueChangeEvent<String> event) {
							String key = event.getValue();
							if (key == null || (passwordCheckingEnabled &&
									 !key.matches("((?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&+=])).{12,}$"))) {
								Window.alert("Please enter a key : "
										+ "\n1) at least 12 characters, "
										+ "\n2) a digit, "
										+ "\n3) an upper case letter, "
										+ "\n4) a lower case letter, and "
										+ "\n5) a special character(!@#$%^&+=).");
								return;
							}
							sensor.setSensorKey(key);

						}
					});

			sensorKeyTextBox.setText(sensor.getSensorKey());
			grid.setWidget(row, 1, sensorKeyTextBox);
			row++;
			
			grid.setText(row,0,"Measurement Type");
			final TextBox measurementTypeTextBox = new TextBox();
			measurementTypeTextBox.setTitle("Enter Swept-frequency or FFT-Power");
			measurementTypeTextBox.addValueChangeHandler( new ValueChangeHandler<String>() {

				@Override
				public void onValueChange(ValueChangeEvent<String> event) {
					String mtype = event.getValue();
					if ( mtype.equals(Defines.FFT_POWER) || mtype.equals(Defines.SWEPT_FREQUENCY)) {
						sensor.setMeasurementType(mtype);
					} else {
						Window.alert("Please enter FFT-Power or Swept-frequency (Case sensitive)");
					}
				}});
			grid.setWidget(row, 1, measurementTypeTextBox);
			row++;
			
			
			grid.setText(row, 0, "Data Retention(months)");
			final TextBox dataRetentionTextBox = new TextBox();
			dataRetentionTextBox.setText(Integer.toString(sensor
					.getDataRetentionDurationMonths()));
			dataRetentionTextBox
					.addValueChangeHandler(new ValueChangeHandler<String>() {

						@Override
						public void onValueChange(ValueChangeEvent<String> event) {
							try {
								String valueStr = event.getValue();
								if (valueStr == null) {
									Window.alert("Please enter integer >= 0");
									return;
								}
								int value = Integer.parseInt(valueStr);
								if (value < 0) {
									Window.alert("Please enter integer >= 0");
									return;
								}
								sensor.setDataRetentionDurationMonths(value);
							} catch (NumberFormatException ex) {
								Window.alert("Please enter positive integer");
								return;

							}

						}

					});
			grid.setWidget(row, 1, dataRetentionTextBox);

			row++;
			grid.setText(row, 0, "Sensor Admin Email");
			final TextBox sensorAdminEmailTextBox = new TextBox();
			sensorAdminEmailTextBox.setText(sensor.getSensorAdminEmail());
			sensorAdminEmailTextBox
					.addValueChangeHandler(new ValueChangeHandler<String>() {

						@Override
						public void onValueChange(ValueChangeEvent<String> event) {
							String email = event.getValue();
							if (!email
									.matches("^[_A-Za-z0-9-]+(\\.[_A-Za-z0-9-]+)*@[A-Za-z0-9-]+(\\.[A-Za-z0-9-]+)*(\\.[A-Za-z]{2,})$")) {
								Window.alert("Please enter valid email address");
								return;
							}
							sensor.setSensorAdminEmail(email);
						}
					});
			grid.setWidget(row, 1, sensorAdminEmailTextBox);

			Button submitButton = new Button("Apply");
			submitButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					if (!sensor.validate()) {
						Window.alert("Error in entry - please enter all fields.");
					} else {
						sensorConfig.setUpdateFlag(true);
						Admin.getAdminService().addSensor(sensor.toString(),
								sensorConfig);
					}

				}
			});

			verticalPanel.add(grid);
			HorizontalPanel hpanel = new HorizontalPanel();
			hpanel.add(submitButton);

			Button cancelButton = new Button("Cancel");
			cancelButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					sensorConfig.redraw();
				}
			});
			hpanel.add(cancelButton);
			
			Button logoffButton = new Button("Log Off");
			logoffButton.addClickHandler(new ClickHandler(){

				@Override
				public void onClick(ClickEvent event) {
					admin.logoff();
				}});
			hpanel.add(logoffButton);
			
			verticalPanel.add(hpanel);
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Problem drawing screen", th);
		}

	}

}

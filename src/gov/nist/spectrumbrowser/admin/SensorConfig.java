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
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserWidget;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

public class SensorConfig extends AbstractSpectrumBrowserWidget implements
		SpectrumBrowserScreen, SpectrumBrowserCallback<String> {

	private Admin admin;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private Grid grid;
	private boolean updateFlag;
	
	ArrayList<Sensor> sensors = new ArrayList<Sensor>();
	class ThresholdButtonHandler implements ClickHandler {
		private Sensor sensor;
		ThresholdButtonHandler(Sensor sensor) {
			this.sensor = sensor;
		}
		@Override
		public void onClick(ClickEvent event) {
			new SensorThresholds(admin, SensorConfig.this,sensor,verticalPanel).draw();
		}}
	

	public SensorConfig(Admin admin) {
		try {
			this.admin = admin;
			Admin.getAdminService().getSensorInfo(this);
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
			Admin.getAdminService().getSensorInfo(this);
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Problem contacting host", th);
			Window.alert("Problem communicating with server");
			admin.logoff();
		}
	}

	@Override
	public void onSuccess(String result) {
		JSONObject jsonObject = JSONParser.parseLenient(result).isObject();
		JSONArray sensorArray = jsonObject.get("sensors").isArray();
		repopulate(sensorArray);
		if (updateFlag) {
			draw();
			updateFlag = false;
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
		HTML title = new HTML("<h3>Please click on the Update button after making changes to update server! </h3>");
		verticalPanel.add(title);
		grid = new Grid(sensors.size()+1,13);
		grid.setText(0,0, "Sensor ID");
		grid.setText(0,1, "Sensor Key");
		grid.setText(0,2, "Data Retention (months)");
		grid.setText(0,3, "Sensor Admin Email");
		grid.setText(0,4, "Last Message Date");
		grid.setText(0,5, "Last Message Type");
		grid.setText(0,6, "Status");
		
		grid.setText(0, 7, "Occupancy Thresholds");
		grid.setText(0, 8, "System Messages");
		grid.setText(0, 9, "Streaming Settings");
		grid.setText(0, 10, "Update Sensor");
		grid.setText(0,11, "Delete");
		grid.setText(0, 12, "Purge");
		for (int i = 0; i < grid.getColumnCount(); i++) {
			grid.getCellFormatter().setStyleName(0, i, "textLabelStyle");
		}
		grid.setCellPadding(2);
		grid.setCellSpacing(2);
		grid.setBorderWidth(2);
		int row = 1;
		for (final Sensor sensor: sensors) {
			
			int col = 0;
			grid.setText(row, col++, sensor.getSensorId()); //0
			final TextBox sensorKeyTextBox = new TextBox();
			
			grid.setWidget(row, col++, sensorKeyTextBox);//1
			sensorKeyTextBox.setText(sensor.getSensorKey());
			sensorKeyTextBox.addValueChangeHandler(new ValueChangeHandler<String>(){

				@Override
				public void onValueChange(ValueChangeEvent<String> event) {
					String newKey = event.getValue();
					if (!sensor.setSensorKey(newKey)) {
						Window.alert("Please enter a key : "
								+ "\n1) at least 12 characters, "
								+ "\n2) a digit, "
								+ "\n3) an upper case letter, "
								+ "\n4) a lower case letter, and "
								+ "\n5) a special character(!@#$%^&+=).");
						sensorKeyTextBox.setText(sensor.getSensorKey());
					}
				}});
			
			final TextBox dataRetentionTextBox = new TextBox();
			dataRetentionTextBox.setValue(Integer.toString(sensor.getDataRetentionDurationMonths()));
			dataRetentionTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {
				@Override
				public void onValueChange(ValueChangeEvent<String> event) {
					try {
						int newRetention = Integer.parseInt(event.getValue());
						if (! sensor.setDataRetentionDurationMonths(newRetention)) {
							Window.alert("Please enter a valid integer >= 1");
							dataRetentionTextBox.setText(Integer.toString(sensor.getDataRetentionDurationMonths()));
 						}
					} catch (Exception ex) {
						Window.alert("Please enter a valid integer >= 1");
					}
				}});
			grid.setWidget(row, col++, dataRetentionTextBox ); //2
			final TextBox adminEmailTextBox = new TextBox();
			adminEmailTextBox.setText(sensor.getSensorAdminEmail());
			adminEmailTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

				@Override
				public void onValueChange(ValueChangeEvent<String> event) {
					String email = event.getValue();
					if (email.matches("^[_A-Za-z0-9-]+(\\.[_A-Za-z0-9-]+)*@[A-Za-z0-9-]+(\\.[A-Za-z0-9-]+)*(\\.[A-Za-z]{2,})$")) {
						sensor.setSensorAdminEmail(email);
					} else {
						Window.alert("please enter a valid email address");
						adminEmailTextBox.setText(sensor.getSensorAdminEmail());
					}
				}});
			
			grid.setWidget(row, col++, adminEmailTextBox);//3
			grid.setText(row, col++, sensor.getSensorLastMessageDate());//4
			grid.setText(row, col++, sensor.getSensorLastMessageType());//5
			grid.setText(row, col++, sensor.getSensorStatus());//6
			
			Button thresholdButton = new Button("Change");
			thresholdButton.addClickHandler(new ClickHandler(){
				@Override
				public void onClick(ClickEvent event) {
					new SensorThresholds(admin,SensorConfig.this,sensor,verticalPanel).draw();
				}});
			
			grid.setWidget(row, col++, thresholdButton); //7
			
			
			Button downloadSysMessages = new Button("Get");
			grid.setWidget(row, col++, downloadSysMessages);//8
			Button streamingButton = new Button("Change");
			grid.setWidget(row,col++,streamingButton); //9
			streamingButton.addClickHandler(new ClickHandler(){

				@Override
				public void onClick(ClickEvent event) {
					 new SetStreamingParams(admin, verticalPanel, sensor, SensorConfig.this).draw();					
				}});
			
			Button updateButton = new Button("Apply");
			updateButton.setStyleName("sendButton");
			updateButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					Admin.getAdminService().updateSensor(sensor.toString(), new SpectrumBrowserCallback<String> () {

						@Override
						public void onSuccess(String result) {
							JSONObject jsonObj = JSONParser.parseLenient(result).isObject();
							if (jsonObj.get("Status").equals("OK")) {
								JSONArray sensorArray = jsonObj.get("sensors").isArray();
								repopulate(sensorArray);
								draw();
 							} else {
								Window.alert("Error Updating Sensor : " + jsonObj.get("ErrorMessage").isString().stringValue());
								redraw();
							}
							
						}

						@Override
						public void onFailure(Throwable throwable) {
							Window.alert("Error communicating with server");
							admin.logoff();
						}});
					
				}});
			
			
			
			grid.setWidget(row, col++, updateButton);//10
			
			Button removeButton = new Button("Delete");
			removeButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					Admin.getAdminService().removeSensor(sensor.getSensorId(), new SpectrumBrowserCallback<String>() {

						@Override
						public void onSuccess(String result) {
							JSONObject jsonObj = JSONParser.parseLenient(result).isObject();
							sensors.clear();
							if (!jsonObj.get("Status").isString().stringValue().equals("OK")) {
								Window.alert("Error Deleting Sensor : " + jsonObj.get("ErrorMessage").isString().stringValue());
							}
							JSONArray sensorArray = jsonObj.get("sensors").isArray();
							repopulate(sensorArray);
							draw();
						}

						@Override
						public void onFailure(Throwable throwable) {
							Window.alert("Error communicating with server");
							admin.logoff();
						}});
					
				}});
			grid.setWidget(row, col++, removeButton);//11
			
			Button purgeButton = new Button("Purge");
			purgeButton.setTitle("WARNING: Removes Sensor and all data associated with it");
			purgeButton.setStyleName("dangerous");
			purgeButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					boolean yes = Window.confirm("Remove the sensor and all associated data?");
					if (yes){
						Admin.getAdminService().purgeSensor(sensor.getSensorId(), new SpectrumBrowserCallback<String>() {
							@Override
							public void onSuccess(String result) {
								JSONObject jsonObj = JSONParser.parseLenient(result).isObject();
								JSONArray sensorArray = jsonObj.get("sensors").isArray();
								repopulate(sensorArray);

								if (!jsonObj.get("Status").isString().stringValue().equals("OK")) {
									Window.alert("Error Deleting Sensor : " + jsonObj.get("ErrorMessage").isString().stringValue());

								} 
								draw();


							}


							@Override
							public void onFailure(Throwable throwable) {
								Window.alert("Error communicating with server");
								admin.logoff();
							}});


					}}});
			grid.setWidget(row, col++, purgeButton);//12

			
			row++;
			
		}
		verticalPanel.add(grid);
		HorizontalPanel buttonPanel = new HorizontalPanel();
		Button addNewSensorButton = new Button("Add new sensor");
		addNewSensorButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				new AddNewSensor(admin,verticalPanel,SensorConfig.this).draw();
			}});
		buttonPanel.add(addNewSensorButton);
		Button logoffButton = new Button("Log Off");
		logoffButton.addClickHandler(new ClickHandler(){

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}});
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

}

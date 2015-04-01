package gov.nist.spectrumbrowser.admin;

import java.util.ArrayList;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

public class AddSensorThreshold {
	
	private VerticalPanel verticalPanel;
	private Threshold threshold;
	private SensorThresholds sensorThresholds;
	private Sensor sensor;
	private Admin admin;
	private SensorConfig sensorConfig;
	
	public AddSensorThreshold(Admin admin, SensorThresholds  sensorThresholds,
			SensorConfig sensorConfig,
			Sensor sensor, VerticalPanel verticalPanel) {
		this.sensorConfig = sensorConfig;
		this.admin = admin;
		this.sensor = sensor;	
		this.threshold = new Threshold();
		this.verticalPanel = verticalPanel;
		this.sensorThresholds = sensorThresholds;
 	}

	public void draw() {
		verticalPanel.clear();
		HTML title = new HTML("<h2>Add a new occupancy threshold for sensor " + sensor.getSensorId()+"</h2>");
		verticalPanel.add(title);
		Grid grid = new Grid(4,2);
		grid.setCellPadding(2);
		grid.setCellSpacing(2);
		grid.setBorderWidth(2);
		int row = 0;
		grid.setText(row, 0, "System To Detect");
		TextBox sysToDetectTextBox = new TextBox();
		sysToDetectTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {
			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String value = event.getValue();
				try {
					threshold.setSystemToDetect(value);
				} catch (IllegalArgumentException ex) {
					Window.alert(ex.getMessage());
				}
				
			}} );
		grid.setWidget(row, 1, sysToDetectTextBox);
		
		row ++;
		
		grid.setText(row, 0, "Min Freq. (Hz)");
		TextBox maxFreqHzTextBox = new TextBox();
		maxFreqHzTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String val = event.getValue();
				try {
					long newVal = Long.parseLong(val);
					threshold.setMinFreqHz(newVal);
				} catch (NumberFormatException ex) {
					Window.alert("Please enter a valid number");
				} catch (IllegalArgumentException ex) {
					Window.alert(ex.getMessage());
				}
			}
		});
		grid.setWidget(row,1,maxFreqHzTextBox);
		
		row ++;
		
		grid.setText(row, 0, "Max Freq. (Hz)");
		TextBox minFreqHzTextBox = new TextBox();
		minFreqHzTextBox.setText(Long.toString(threshold.getMaxFreqHz()));
		minFreqHzTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {
			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String val = event.getValue();
				try {
					long newVal = Long.parseLong(val);
					threshold.setMaxFreqHz(newVal);
				} catch (NumberFormatException ex) {
					Window.alert("Please enter a valid number");
				} catch (IllegalArgumentException ex) {
					Window.alert(ex.getMessage());
				}
			}
		});
		grid.setWidget(row,1,minFreqHzTextBox);
		
		row++;
		
		grid.setText(row, 0, "Threshold (dBm/Hz)");
		TextBox thresholdTextBox = new TextBox();
		thresholdTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String val = event.getValue();
				try {
					double newValue = Double.parseDouble(val);
					threshold.setThresholdDbmPerHz(newValue);
				} catch (NumberFormatException ex) {
					Window.alert("Please enter a valid number");
				} catch (IllegalArgumentException ex) {
					Window.alert(ex.getMessage());
				}
			}});
		grid.setWidget(row, 1, thresholdTextBox);
		
		verticalPanel.add(grid);
		HorizontalPanel horizontalPanel = new HorizontalPanel();
		Button applyButton = new Button("Apply");
		horizontalPanel.add(applyButton);
		applyButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				if (!threshold.validate()) {
					Window.alert("Error in one or more entries");
				} else {				
					sensor.addNewThreshold(AddSensorThreshold.this.threshold.getSystemToDetect(), threshold.getThreshold());
					Admin.getAdminService().updateSensor(sensor.toString(), sensorConfig);

					sensorThresholds.draw();
				}
				
			}});
		
		Button cancelButton = new Button("Cancel");
		horizontalPanel.add(cancelButton);
		cancelButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				sensorThresholds.draw();
			}});
		
		Button logoffButton = new Button("Log Off");
		horizontalPanel.add(logoffButton);
		logoffButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}});
		
		verticalPanel.add(horizontalPanel);
 		
	}

}

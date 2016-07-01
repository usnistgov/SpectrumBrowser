/*
* Conditions Of Use 
* 
* This software was developed by employees of the National Institute of
* Standards and Technology (NIST), and others. 
* This software has been contributed to the public domain. 
* Pursuant to title 15 Untied States Code Section 105, works of NIST
* employees are not subject to copyright protection in the United States
* and are considered to be in the public domain. 
* As a result, a formal license is not needed to use this software.
* 
* This software is provided "AS IS."  
* NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
* OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
* AND DATA ACCURACY.  NIST does not warrant or make any representations
* regarding the use of the software or the results thereof, including but
* not limited to the correctness, accuracy, reliability or usefulness of
* this software.
*/
package gov.nist.spectrumbrowser.admin;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
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

public class SensorIdentity {
	private Sensor sensor;
	private SensorConfig sensorConfig;
	private Grid grid;
	private VerticalPanel verticalPanel;
	private Admin admin;

	public SensorIdentity(Admin admin, SensorConfig sensorConfig, Sensor sensor, VerticalPanel verticalPanel) {
		this.sensor = sensor;
		this.sensorConfig = sensorConfig;
		this.verticalPanel = verticalPanel;
		this.admin = admin;
	}
	
	public void draw() {
		verticalPanel.clear();
		HTML html = new HTML("<h3>Sensor Identity</h3>");
		verticalPanel.add(html);
		this.grid = new Grid(5	,2);
		
		

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
		
		verticalPanel.add(grid);
		int row = 0;
		grid.setText(row, 0, "Sensor Name:");
		grid.setText(row, 1, sensor.getSensorId()); // 0
		
		row++;
		
		grid.setText(row, 0, "Sensor Key:");
		final TextBox sensorKeyTextBox = new TextBox();

		grid.setWidget(row, 1, sensorKeyTextBox);
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
								sensor.toString(), sensorConfig);
					}
				});
		
		row++;

		grid.setText(row, 0, "Measurement Type:");
		grid.setText(row, 1, sensor.getMeasurementType());
		row++;
		
		grid.setText(row, 0, "Sensor Admin Email:");
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
								sensor.toString(), sensorConfig);
					}
				});
		grid.setWidget(row, 1, adminEmailTextBox);
		row++;
		
		boolean isStreamingEnabled = sensor.isStreamingEnabled();
		final CheckBox checkBox = new CheckBox();
		checkBox.setValue(isStreamingEnabled);
		grid.setText(row, 0, "isStreamingEnabled");
		grid.setWidget(row, 1, checkBox);
		checkBox.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				boolean currentState = sensor.isStreamingEnabled();
				boolean newState = !currentState;
				checkBox.setValue(newState);
				sensor.setStreamingEnabled(newState);
				Admin.getAdminService().updateSensor(
						sensor.toString(), sensorConfig);
			}});
		
		HorizontalPanel buttonPanel = new HorizontalPanel();
		
		Button okButton = new Button("Done");
		buttonPanel.add(okButton);
		okButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				   sensorConfig.draw();
			}});
		Button logoffButton = new Button("Log Off");
		logoffButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}});
		buttonPanel.add(logoffButton);
		verticalPanel.add(buttonPanel);

		

	}
}

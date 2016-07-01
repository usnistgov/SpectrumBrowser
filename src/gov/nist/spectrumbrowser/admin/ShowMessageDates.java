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
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.VerticalPanel;

public class ShowMessageDates {
	Sensor sensor;
	Admin admin;
	SensorConfig sensorConfig;
	VerticalPanel verticalPanel;

	public ShowMessageDates(Admin admin, SensorConfig sensorConfig,
			Sensor sensor, VerticalPanel verticalPanel) {
		this.verticalPanel = verticalPanel;
		this.sensor = sensor;
		this.sensorConfig = sensorConfig;
		this.admin = admin;
	}

	public void draw() {
		HTML html = new HTML("<h3>Show Meta-data: Local time of message reception for sensor "
				+ sensor.getSensorId() + "</h3>");
		verticalPanel.clear();
		verticalPanel.add(html);
		Grid grid = new Grid(6, 3);
		grid.setCellPadding(3);
		grid.setCellSpacing(3);
		grid.setBorderWidth(3);

		JSONObject messageDates = sensor.getMessageDates();
		if (messageDates != null) {
			String firstLocationMessageDate = messageDates
					.get("FIRST_LOCATION_MESSAGE_DATE").isString()
					.stringValue();
			String lastLocationMessageDate = messageDates
					.get("LAST_LOCATION_MESSAGE_DATE").isString().stringValue();
			String firstDataMessageDate = messageDates
					.get("FIRST_DATA_MESSAGE_DATE").isString().stringValue();
			String lastDataMessageDate = messageDates
					.get("LAST_DATA_MESSAGE_DATE").isString().stringValue();
			String firstSystemMessageDate = messageDates
					.get("FIRST_SYSTEM_MESSAGE_DATE").isString().stringValue();
			String lastSystemMessageDate = messageDates
					.get("LAST_SYSTEM_MESSAGE_DATE").isString().stringValue();

			final JSONObject messageJsons = sensor.getMessageJsons();

			int row = 0;
			grid.setText(row, 0, "First System Message");
			grid.setText(row, 1, firstSystemMessageDate);
			Button firstSystemMessage = new Button("Show Message");
			firstSystemMessage
					.setTitle("Shows the First System Message in the Database");
			firstSystemMessage.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					new JSONViewer(messageJsons, "FIRST_SYSTEM_MESSAGE", admin,
							ShowMessageDates.this, verticalPanel, sensor)
							.draw();
				}
			});
			grid.setWidget(row, 2, firstSystemMessage);
			row++;

			grid.setText(row, 0, "Last System Message");
			grid.setText(row, 1, lastSystemMessageDate);
			Button lastSystemMessage = new Button("Show Message");
			lastSystemMessage
					.setTitle("Shows the Last System Message in the Database");
			lastSystemMessage.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					new JSONViewer(messageJsons, "LAST_SYSTEM_MESSAGE", admin,
							ShowMessageDates.this, verticalPanel, sensor)
							.draw();
				}
			});
			grid.setWidget(row, 2, lastSystemMessage);
			row++;

			grid.setText(row, 0, "First Location Message");
			grid.setText(row, 1, firstLocationMessageDate);
			Button firstLocationMessage = new Button("Show Message");
			firstLocationMessage
					.setTitle("Shows the First Location Message in the Database");
			firstLocationMessage.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					new JSONViewer(messageJsons, "FIRST_LOCATION_MESSAGE",
							admin, ShowMessageDates.this, verticalPanel, sensor)
							.draw();
				}
			});
			grid.setWidget(row, 2, firstLocationMessage);
			row++;

			grid.setText(row, 0, "Last Location Message");
			grid.setText(row, 1, lastLocationMessageDate);
			Button lastLocationMessage = new Button("Show Message");
			lastLocationMessage
					.setTitle("Shows the Last Location Message in the Database");
			lastLocationMessage.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					new JSONViewer(messageJsons, "LAST_LOCATION_MESSAGE",
							admin, ShowMessageDates.this, verticalPanel, sensor)
							.draw();
				}
			});
			grid.setWidget(row, 2, lastLocationMessage);
			row++;

			grid.setText(row, 0, "First Data Message");
			grid.setText(row, 1, firstDataMessageDate);
			Button firstDataMessage = new Button("Show Message");
			firstDataMessage
					.setTitle("Shows the First Data Message in the Database");
			firstDataMessage.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					new JSONViewer(messageJsons, "FIRST_DATA_MESSAGE", admin,
							ShowMessageDates.this, verticalPanel, sensor)
							.draw();
				}
			});
			grid.setWidget(row, 2, firstDataMessage);
			row++;

			grid.setText(row, 0, "Last Data Message");
			grid.setText(row, 1, lastDataMessageDate);
			Button lastDataMessage = new Button("Show Message");
			lastDataMessage
					.setTitle("Shows the Last Data Message in the Database");
			lastDataMessage.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					new JSONViewer(messageJsons, "LAST_DATA_MESSAGE", admin,
							ShowMessageDates.this, verticalPanel, sensor)
							.draw();
				}
			});
			grid.setWidget(row, 2, lastDataMessage);
			row++;

			for (int i = 0; i < grid.getRowCount(); i++) {
				grid.getCellFormatter().setStyleName(i, 0, "textLabel");
			}
			verticalPanel.add(grid);
		} else {
			Window.alert("No messages found");
		}

		HorizontalPanel hpanel = new HorizontalPanel();

		Button okButton = new Button("OK");
		okButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				sensorConfig.redraw();

			}
		});
		hpanel.add(okButton);

		Button logoffButton = new Button("Log Off");
		logoffButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}
		});

		hpanel.add(logoffButton);
		verticalPanel.add(hpanel);

	}

}

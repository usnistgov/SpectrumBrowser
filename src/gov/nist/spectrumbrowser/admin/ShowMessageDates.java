package gov.nist.spectrumbrowser.admin;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
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
		HTML html = new HTML("<h3>Local time of message reception for sensor " + sensor.getSensorId()+ "</h3>");
		verticalPanel.clear();
		verticalPanel.add(html);
		Grid grid = new Grid(6,2);
		grid.setCellPadding(2);
		grid.setCellSpacing(2);
		grid.setBorderWidth(2);
		
	
		JSONObject messageDates = sensor.getMessageDates();
		String firstLocationMessageDate = messageDates.get("FIRST_LOCATION_MESSAGE").isString().stringValue();
		String lastLocationMessageDate = messageDates.get("LAST_LOCATION_MESSAGE").isString().stringValue();
		String firstDataMessageDate  = messageDates.get("FIRST_DATA_MESSAGE_DATE").isString().stringValue();
		String lastDataMessageDate = messageDates.get("LAST_DATA_MESSAGE_DATE").isString().stringValue();
		String firstSystemMessageDate = messageDates.get("FIRST_SYSTEM_MESSAGE_DATE").isString().stringValue();
		String lastSystemMessageDate = messageDates.get("LAST_SYSTEM_MESSAGE_DATE").isString().stringValue();
		
		int row = 0;
		grid.setText(row, 0, "First System Message");
		grid.setText(row, 1, firstSystemMessageDate);
		row++;
		grid.setText(row, 0, "Last System Message");
		grid.setText(row, 1, lastSystemMessageDate);
		row++;
		grid.setText(row, 0, "First Location Message");
		grid.setText(row, 1, firstLocationMessageDate);
		row++;
		grid.setText(row,0,"Last Location Message");
		grid.setText(row,1,lastLocationMessageDate);
		row++;
		grid.setText(row,0,"First Data Message");
		grid.setText(row,1,firstDataMessageDate);
		row++;
		grid.setText(row,0,"Last Data Message");
		grid.setText(row,1,lastDataMessageDate);
		row++;
		
		for (int i = 0 ; i < grid.getRowCount(); i++) {
			grid.getCellFormatter().setStyleName(i, 0, "textLabel");
		}
		verticalPanel.add(grid);
		
		HorizontalPanel hpanel = new HorizontalPanel();
		
		Button okButton = new Button("OK");
		okButton.addClickHandler(new ClickHandler(){

			@Override
			public void onClick(ClickEvent event) {
				sensorConfig.redraw();
				
			}});
		hpanel.add(okButton);
		
		Button logoffButton = new Button("Log Off");
		logoffButton.addClickHandler (new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}});
		
		hpanel.add(logoffButton);
		verticalPanel.add(hpanel);
		
		
		
		
	}

}

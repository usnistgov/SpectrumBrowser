package gov.nist.spectrumbrowser.admin;

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.VerticalPanel;


public class SensorThresholds {

	private VerticalPanel verticalPanel;
	private Sensor sensor;
	private SensorConfig sensorConfig;
	private Grid grid;
	private Admin admin;

	public SensorThresholds(Admin admin, SensorConfig sensorConfig, Sensor sensor,
			VerticalPanel verticalPanel) {
		this.verticalPanel = verticalPanel;
		this.sensor = sensor;
		this.sensorConfig = sensorConfig;
		this.admin = admin;
	}

	class DeleteThresholdClickHandler implements ClickHandler {
		private String systemToDetect;

		DeleteThresholdClickHandler(String systemToDetect) {
			this.systemToDetect = systemToDetect;
		}

		@Override
		public void onClick(ClickEvent event) {
			sensor.deleteThreshold(systemToDetect);
			draw();
		}
	}

	public void draw() {

		verticalPanel.clear();
		HTML html = new HTML("<H2>Sensor Thresholds for occupancy computation for sensor : " + sensor.getSensorId()+ "</H2>");
		verticalPanel.add(html);
		JSONObject sensorThresholds = sensor.getThresholds();
		
		Grid grid = new Grid(sensorThresholds.keySet().size()+1,5);
		grid.setBorderWidth(2);
		grid.setCellPadding(2);
		grid.setCellSpacing(2);
		grid.setText(0, 0, "System To Detect");
		grid.setText(0, 1, "Min Freq (Hz)");
		grid.setText(0, 2, "Max Freq (Hz)");
		grid.setText(0, 3, "Threshold (dBm/Hz).");
		grid.setText(0, 4, "Delete Threshold");
		grid.setBorderWidth(2);
		grid.setCellPadding(2);
		grid.setCellSpacing(2);
		for (int i = 0 ; i < grid.getColumnCount(); i++){
			grid.getCellFormatter().setStyleName(0,i , "textLabelStyle");
		}


		int row = 1;
		for (String key : sensorThresholds.keySet()) {
			Threshold threshold = new Threshold(sensorThresholds.get(key).isObject());
			grid.setText(row, 0, threshold.getSystemToDetect());
			grid.setText(row, 1, Long.toString(threshold.getMaxFreqHz()));
			grid.setText(row, 2, Long.toString(threshold.getMinFreqHz()));
			grid.setText(row, 3, Double.toString(threshold.getThresholdDbmPerHz()));
			Button deleteButton = new Button("Delete Threshold");
			deleteButton.addClickHandler( new DeleteThresholdClickHandler(threshold.getSystemToDetect()));
			grid.setWidget(row, 4, deleteButton);
			row++;
		}
		verticalPanel.add(grid);
		HorizontalPanel horizontalPanel = new HorizontalPanel();
		Button addButton = new Button("Add Threshold");
		addButton.addClickHandler(new ClickHandler () {

			@Override
			public void onClick(ClickEvent event) {
				new AddSensorThreshold(admin,SensorThresholds.this, sensorConfig, sensor,verticalPanel).draw();
			}
		});
		horizontalPanel.add(addButton);
		

		Button doneButton = new Button("Done");
		doneButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				sensorConfig.draw();
			}} );
		
		horizontalPanel.add(doneButton);
		
		
		
		Button logoffButton = new Button("Log Off");
		logoffButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}});
		
		horizontalPanel.add(logoffButton);
		
		verticalPanel.add(horizontalPanel);
		
	}


}
	
	

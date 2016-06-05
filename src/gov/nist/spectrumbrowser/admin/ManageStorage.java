package gov.nist.spectrumbrowser.admin;

import java.util.ArrayList;
import java.util.logging.Level;
import java.util.logging.Logger;

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

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
import com.google.gwt.user.client.ui.VerticalPanel;

public class ManageStorage implements SpectrumBrowserCallback<String> {
	private Admin admin;
	private SensorConfig sensorConfig;
	private VerticalPanel verticalPanel;
	private Sensor sensor;
	protected boolean updateFlag;
	private ArrayList<Sensor> sensors;
	private HTML progress;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	public ManageStorage(Admin admin, VerticalPanel verticalPanel,
		ArrayList<Sensor> sensors,	Sensor sensor, SensorConfig sensorConfig) {
		this.admin = admin;
		this.sensorConfig = sensorConfig;
		this.verticalPanel = verticalPanel;
		this.sensor = sensor;
		this.sensors = sensors;
		this.progress = new HTML(
				"<h3>Removing timed out data records. Please wait. This can take a while. </h3>");
	}
	
	public void draw() {
		verticalPanel.clear();
		
		HTML title = new HTML("<h3>Sensor Storage Management </h3>");
		verticalPanel.add(title);
		
		Grid grid = new Grid(2,2);
		grid.setText(0, 0, "Data Retention Duration (months)");
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
								Window.alert("Please enter a valid integer >= 0");
								dataRetentionTextBox.setText(Integer.toString(sensor
										.getDataRetentionDurationMonths()));
								return;
							}
							Admin.getAdminService().updateSensor(
									sensor.toString(), ManageStorage.this);
						} catch (Exception ex) {
							Window.alert("Please enter a valid integer >= 0");
						}
					}
				});
		grid.setWidget(0, 1, dataRetentionTextBox);
		
		Button cleanupButton = new Button("Garbage Collect");
		cleanupButton.setTitle("Removes timed out data");
		cleanupButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {

				if (sensor.getSensorStatus().equals("ENABLED")) {
					Window.alert("Please toggle sensor status");
					return;
				}
				boolean yes = Window
						.confirm("This can take a while. Please ensure there are no active user sessions. "
								+ "Deleted records can't be reclaimed.");

				if (yes) {					
					verticalPanel.add(progress);
					ManageStorage.this.updateFlag = true;
					Admin.getAdminService().garbageCollect(
							sensor.getSensorId(), ManageStorage.this);
				}
			}
		});
		
		
		verticalPanel.add(grid);
		
		HorizontalPanel hpanel = new HorizontalPanel();
		hpanel.add(cleanupButton);
		
		
		Button done = new Button("Done");
		done.addClickHandler( new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				Window.alert("Please re-enable sensor on sensor management page");
				sensorConfig.draw();
				
			}});
		
		hpanel.add(done);
		
		Button logoffButton = new Button("Log out");
		logoffButton.addClickHandler( new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
				
			}} );
		hpanel.add(logoffButton);
		verticalPanel.add(hpanel);

	}
	
	
	private void repopulate(JSONArray sensorArray) {
		
		sensors.clear();
		for (int i = 0; i < sensorArray.size(); i++) {
			JSONObject sensorObj = sensorArray.get(i).isObject();
			Sensor sensor = new Sensor(sensorObj);
			sensors.add(sensor);
		}
	}
	
	@Override
	public void onSuccess(String result) {
		JSONObject jsonObject = JSONParser.parseLenient(result).isObject();
		String flag = jsonObject.get("status").isString().stringValue();
		//logger.finer(result);
		verticalPanel.remove(progress);
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
		Window.alert("Problem communicating with server");
		admin.logoff();
		logger.log(Level.SEVERE,"Error in ManageStorage",throwable);
		
	}
}

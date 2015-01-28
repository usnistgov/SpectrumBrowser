package gov.nist.spectrumbrowser.admin;

import java.util.ArrayList;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.TextBox;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserWidget;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

public class SensorConfig extends AbstractSpectrumBrowserWidget implements
		SpectrumBrowserScreen, SpectrumBrowserCallback<String> {

	private Admin admin;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private Grid grid;
	private int nSensors;
	ArrayList<Sensor> sensors = new ArrayList<Sensor>();
	class Sensor {
		
		private JSONObject sensorObj;

		
		Sensor (JSONObject sensorObj) {
			this.sensorObj  = sensorObj;
		}

		void setThreshold(JSONObject threshold) {
			sensorObj.put("threshold", threshold);
		}
		
		JSONObject getThreshold() {
			return sensorObj.get("threshold").isObject();
		}
		
		String getSensorId() {
			return sensorObj.get("sensorId").isString().stringValue();
		}
		
		String getSensorKey() {
			return sensorObj.get("sensorKey").isString().stringValue();
		}
		
		void setSensorKey(String sensorKey) {
			sensorObj.put("sensorKey", new JSONString(sensorKey));
		}
		
		String getSensorAdminEmail() {
			return sensorObj.get("sensorAdminEmail").isString()
					.stringValue();
		}
		
		void setSensorAdminEmail(String sensorAdminEmail) {
			sensorObj.put("sensorAdminEmail", new JSONString(sensorAdminEmail));
		}
		
		String getSensorAccountStatus() {
			return sensorObj.get("sensorStatus").isString().stringValue();
		}
		
		String getSensorLastMessageDate() {
			return sensorObj.get("lastDataMessageDate")
				.isString().stringValue();
		}
		
		String getSensorLastMessageType() {
			return sensorObj.get("lastMessageType").isString().stringValue();
		}
		
		int getDataRetentionDurationMonths() {
			return (int) sensorObj.get("dataRetentionDurationMonths").isNumber().doubleValue();
		}
		
		
	}
	class ThresholdButtonHandler implements ClickHandler {
		private Sensor sensor;
		ThresholdButtonHandler(Sensor sensor) {
			this.sensor = sensor;
		}
		@Override
		public void onClick(ClickEvent event) {
			new SensorThreshold(SensorConfig.this,sensor.getThreshold(),verticalPanel).draw();
			
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

	@Override
	public void onSuccess(String result) {
		JSONObject jsonObject = JSONParser.parseLenient(result).isObject();
		JSONArray sensorArray = jsonObject.get("sensors").isArray();
		for (int i = 0; i < sensorArray.size(); i++) {
			JSONObject sensorObj = sensorArray.get(i).isObject();
			Sensor sensor = new Sensor(sensorObj);
				this.sensors.add(sensor);
		}
		draw();

	}

	@Override
	public void onFailure(Throwable throwable) {
		// TODO Auto-generated method stub

	}

	@Override
	public void draw() {
		grid = new Grid(sensors.size()+1,13);
		grid.setText(0,0, "Sensor ID");
		grid.setText(0,1, "Sensor Key");
		grid.setText(0,3, "Data Retention (months)");
		grid.setText(0,4, "Sensor Admin Email");
		grid.setText(0,5, "Sensor Registration Status");
		grid.setText(0,7, "Last Message Date");
		grid.setText(0,8, "Last Message Type");
		grid.setText(0,9, "Delete");
		int row = 1;
		for (Sensor sensor: sensors) {
			int col = 0;
			grid.setText(row, col++, sensor.getSensorId());
			grid.setText(row, col++, sensor.getSensorKey());
			Button thresholdButton = new Button("Threshold");
			grid.setWidget(row, col++, thresholdButton);
			
			TextBox dataRetentionTextBox = new TextBox();
			dataRetentionTextBox.setValue(Integer.toString(sensor.getDataRetentionDurationMonths()));
			// TODO -- add ValueChangeHandler
			grid.setWidget(row, col++, dataRetentionTextBox );
			TextBox adminEmailTextBox = new TextBox();
			adminEmailTextBox.setText(sensor.getSensorAdminEmail());
			grid.setWidget(row, col++, adminEmailTextBox);
			grid.setText(row, col++, sensor.getSensorAccountStatus());
			grid.setText(row, col++, sensor.getSensorLastMessageDate());
			grid.setText(row, col++, sensor.getSensorLastMessageType());
			Button removeButton = new Button("Remove Sensor");
			grid.setWidget(row, col++, removeButton);
			Button updateButton = new Button("Update Sensor");
			grid.setWidget(row, col++, updateButton);
			
		}
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

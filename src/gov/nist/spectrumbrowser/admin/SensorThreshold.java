package gov.nist.spectrumbrowser.admin;

import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

public class SensorThreshold {
	
	private VerticalPanel verticalPanel;
	private Threshold threshold;
	
	class Threshold {
		private JSONObject threshold;

		Threshold (JSONObject threshold) {
			this.threshold = threshold;
		}
		public String getSystemToDetect() {
			if (threshold.containsKey("systemToDetect")) {
				return threshold.get("systemToDetect").isString().stringValue();
			} else {
				return "UNKNOWN";
			}
		}
		
		public void setSystemToDetect(String systemToDetect) {
			if ( systemToDetect == null || systemToDetect.equals("")) 
				throw new IllegalArgumentException("Attempting to set Illegal value " + systemToDetect);
			threshold.put("systemToDetect", new JSONString(systemToDetect));
		}
		
		public void setMaxFreqHz(long maxFreqHz) {
			threshold.put("maxFreqHz", new JSONNumber(maxFreqHz));
		}
		
		public long getMaxFreqHz() {
			if (threshold.containsKey("maxFreqHz")) {
				return (long) threshold.get("maxFreqHz").isNumber().doubleValue();
			} else {
				return -1;
			}
		}
		public void setMinFreqHz( long minFreqHz) {
			if (minFreqHz<=0) 
				throw new IllegalArgumentException("Attempting to set Illegal value "  + minFreqHz);
			threshold.put("minFreqHz", new JSONNumber(minFreqHz));
		}
		
		public long getMinFreqHz() {
			if (threshold.containsKey("minFreqHz")) {
				return (long) threshold.get("minFreqHz").isNumber().doubleValue();
			} else {
				return -1;
			}
		}
		
		public void setThresholdDbmPerHz(double dbmPerHz) {
			if ( dbmPerHz <= 0) 
				throw new IllegalArgumentException("Attempting to set Illegal value " + dbmPerHz);
			threshold.put("thresholdDbmPerHz", new JSONNumber(dbmPerHz));
		}
		
		public double getThresholdDbmPerHz() {
			if ( threshold.containsKey("thresholdDbmPerHz")) {
					return threshold.get("thresholdDbmPerHz").isNumber().doubleValue();
			} else {
				return -1;
			}
		}
		
		public boolean validate() {
			if (getMaxFreqHz() <= 0 || getMinFreqHz() <= 0 || getSystemToDetect().equals("UNKNOWN") ||
					getMinFreqHz() >= getMaxFreqHz()) {
				return false;
			} else {
				return true;
			}
		}
	}

	public SensorThreshold(SensorConfig  sensorConfig,
			JSONObject threshold, VerticalPanel verticalPanel) {
		this.threshold = new Threshold(threshold);
		this.verticalPanel = verticalPanel;
 	}

	public void draw() {
		verticalPanel.clear();
		Grid grid = new Grid(4,2);
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
					threshold.setMaxFreqHz(newVal);
				} catch (NumberFormatException ex) {
					Window.alert("Please enter a valid number");
				} catch (IllegalArgumentException ex) {
					Window.alert(ex.getMessage());
				}
			}
		});
		grid.setWidget(row,1,maxFreqHzTextBox);
		
		row ++;
		
		grid.setText(row, 0, "Max Freq. Hz.");
		TextBox minFreqHzTextBox = new TextBox();
		minFreqHzTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {
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
		grid.setWidget(row,1,minFreqHzTextBox);
		
		row++;
		
		grid.setText(row, 0, "Threshold (dbM/Hz)");
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
		
		
		

		
 		
	}

}

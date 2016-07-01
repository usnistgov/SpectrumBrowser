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
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

public class AddFftPowerSensorBand {
	
	private VerticalPanel verticalPanel;
	private FftPowerBand threshold;
	private FftPowerSensorBands sensorThresholds;
	private Sensor sensor;
	private Admin admin;
	private SensorConfig sensorConfig;
	private TextBox channelCountTextBox;
	private TextBox thresholdTextBox;
	private boolean verified = false;
	
	public AddFftPowerSensorBand(Admin admin, FftPowerSensorBands  sensorThresholds,
			SensorConfig sensorConfig,
			Sensor sensor, VerticalPanel verticalPanel) {
		this.sensorConfig = sensorConfig;
		this.admin = admin;
		this.sensor = sensor;	
		this.threshold = new FftPowerBand(sensor);
		this.verticalPanel = verticalPanel;
		this.sensorThresholds = sensorThresholds;
 	}

	public void draw() {
		verticalPanel.clear();
		HTML title = new HTML("<h2>Add a new band for sensor " + sensor.getSensorId()+"</h2>");
		verticalPanel.add(title);
		final Grid grid = new Grid(8,3);
		grid.setCellPadding(2);
		grid.setCellSpacing(2);
		grid.setBorderWidth(2);
		grid.setText(0, 0, "Setting");
		grid.setText(0, 1, "Value");
		grid.setText(0, 2, "Info");
		for (int i = 0; i < grid.getRowCount(); i++) {
			for (int j = 0; j < grid.getColumnCount(); j++) {
				grid.getCellFormatter().setHorizontalAlignment(i, j,
						HasHorizontalAlignment.ALIGN_CENTER);
				grid.getCellFormatter().setVerticalAlignment(i, j,
						HasVerticalAlignment.ALIGN_MIDDLE);
			}
		}
		int row = 1;
		grid.setText(row, 0, "System To Detect");
		TextBox sysToDetectTextBox = new TextBox();
		sysToDetectTextBox.setValue(threshold.getSystemToDetect());
		sysToDetectTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {
			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String value = event.getValue();
				verified = false;
				try {
					threshold.setSystemToDetect(value);
				} catch (IllegalArgumentException ex) {
					Window.alert(ex.getMessage());
				}
				
			}} );
		grid.setWidget(row, 1, sysToDetectTextBox);
		
		row ++;
		
		grid.setText(row, 0, "Min Freq. (Hz)");
		TextBox minFreqHzTextBox = new TextBox();
		minFreqHzTextBox.setEnabled(true);

		minFreqHzTextBox.setText(Long.toString(threshold.getMinFreqHz()));
		minFreqHzTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String val = event.getValue();
				verified = false;
				try {
					long newVal = (long) Double.parseDouble(val);
					threshold.setMinFreqHz(newVal);
				} catch (NumberFormatException ex) {
					Window.alert("Please enter a valid number");
				} catch (IllegalArgumentException ex) {
					Window.alert(ex.getMessage());
				}
			}
		});
		grid.setWidget(row,1,minFreqHzTextBox); //2
		
		row ++;
		
		grid.setText(row, 0, "Max Freq. (Hz)");
		TextBox maxFreqHzTextBox = new TextBox();
		maxFreqHzTextBox.setEnabled(true);
		maxFreqHzTextBox.setText(Long.toString(threshold.getMaxFreqHz()));
		maxFreqHzTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {
			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String val = event.getValue();
				verified = false;
				try {
					long newVal = (long)Double.parseDouble(val);
					threshold.setMaxFreqHz(newVal);
					if (threshold.getMinFreqHz() >= 0 && threshold.getMaxFreqHz() > 0) {
						channelCountTextBox.setEnabled(true);
					}
				} catch (NumberFormatException ex) {
					Window.alert("Please enter a valid number");
				} catch (IllegalArgumentException ex) {
					Window.alert(ex.getMessage());
				}
			}
		});
		grid.setWidget(row,1,maxFreqHzTextBox);//3
		
		row++;
		
		grid.setText(row,0,"Channel Count");
		channelCountTextBox = new TextBox();
		channelCountTextBox.setEnabled(false);
		channelCountTextBox.setText(Long.toString(threshold.getChannelCount()));
		channelCountTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String val = event.getValue();
				verified = false;
				try {
					long newVal = Long.parseLong(val);
					threshold.setChannelCount(newVal);
					
					thresholdTextBox.setEnabled(true);
				} catch (NumberFormatException ex) {
					Window.alert("Please enter a valid number");
				} catch (IllegalArgumentException ex) {
					Window.alert(ex.getMessage());
				}
			}});
		grid.setWidget(row,1,channelCountTextBox);//4
		
		row++;

		grid.setText(row, 0, "Occupancy Threshold (dBm/Hz)");
		thresholdTextBox = new TextBox();
		thresholdTextBox.setText("UNKNOWN");
		thresholdTextBox.setEnabled(false);
		thresholdTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String val = event.getValue();
				verified = false;
				try {
					double newValue = Double.parseDouble(val);
					threshold.setThresholdDbmPerHz(newValue);
					
				} catch (NumberFormatException ex) {
					Window.alert("Please enter a valid number");
				} catch (IllegalArgumentException ex) {
					Window.alert(ex.getMessage());
				}
			}});
		grid.setWidget(row, 1, thresholdTextBox); //5
		row++;
		
		grid.setText(row, 0, "Sampling Rate (Samples/S) ");
		TextBox samplingRateTextBox = new TextBox();
		samplingRateTextBox.addValueChangeHandler(new ValueChangeHandler<String>(){

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String val = event.getValue();
				verified = false;
				try {
					long newVal = (long)Double.parseDouble(val);
					threshold.setSamplingRate(newVal);
				} catch (NumberFormatException ex) {
					Window.alert("Please enter a valid number");
				} catch (IllegalArgumentException ex) {
					Window.alert(ex.getMessage());
				}
			}
			});
		
		grid.setWidget(row, 1, samplingRateTextBox);//6
		row++;
		
		
		grid.setText(row, 0, "FFT Size");
		TextBox fftSizeTextBox = new TextBox();
		fftSizeTextBox.addValueChangeHandler(new ValueChangeHandler<String>(){

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String val = event.getValue();
				verified = false;
				try {
					long newVal = Long.parseLong(val);
					threshold.setFftSize(newVal);
				} catch (NumberFormatException ex) {
					Window.alert("Please enter a valid number");
				} catch (IllegalArgumentException ex) {
					Window.alert(ex.getMessage());
				}
			}
			});
		
		grid.setWidget(row, 1, fftSizeTextBox);
		row++;
				
	
		
		verticalPanel.add(grid);
		HorizontalPanel horizontalPanel = new HorizontalPanel();
		final Button okButton = new Button("Check Entries");
		okButton.setTitle("Check entered values and print additional information");
		final Button applyButton = new Button("Apply");
		applyButton.setTitle("Please Chek Entries and Apply to update server entries");
		applyButton.setEnabled(false);
		horizontalPanel.add(okButton);
		okButton.addClickHandler( new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				// TODO Auto-generated method stub
				if (!threshold.validate()) {
					Window.alert("Error in one or more entries");
				} else {
					long channelCount = threshold.getChannelCount();
					grid.setText(4, 2, "Resolution BW = " + ((threshold.getMaxFreqHz() - threshold.getMinFreqHz())/ (1000*channelCount))
							+ " " + " KHz");
					double thresholdDbmPerHz = threshold.getThresholdDbmPerHz();
					double resolutionBw = (threshold.getMaxFreqHz() - threshold.getMinFreqHz())/channelCount;
					grid.setText(5, 2, "Threshold (dBm) = " + (thresholdDbmPerHz + 10*Math.log10(resolutionBw)));
					verified = true;
					applyButton.setEnabled(true);
				}
			}
		
		});
		
		horizontalPanel.add(applyButton);
		applyButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				if (!threshold.validate()) {
					Window.alert("Error in one or more entries");
				} else {
					sensor.addNewThreshold(AddFftPowerSensorBand.this.threshold.getSystemToDetect(), threshold.getThreshold());
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




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

import gov.nist.spectrumbrowser.common.Defines;
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
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HTMLTable.CellFormatter;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

public class SweptFrequencySensorBands {

	private VerticalPanel verticalPanel;
	private Sensor sensor;
	private SensorConfig sensorConfig;
	private Admin admin;

	public SweptFrequencySensorBands(Admin admin, SensorConfig sensorConfig,
			Sensor sensor, VerticalPanel verticalPanel) {
		this.verticalPanel = verticalPanel;
		this.sensor = sensor;
		this.sensorConfig = sensorConfig;
		this.admin = admin;
	}

	class DeleteThresholdClickHandler implements ClickHandler {
		SweptFrequencyBand threshold;

		DeleteThresholdClickHandler(SweptFrequencyBand threshold) {
			this.threshold = threshold;
		}

		@Override
		public void onClick(ClickEvent event) {
			sensor.deleteThreshold(threshold);
			Admin.getAdminService().updateSensor(sensor.toString(),
					sensorConfig);
			draw();
		}
	}

	public void draw() {

		verticalPanel.clear();
		HTML html = new HTML("<H2>Bands for sensor : " + sensor.getSensorId()
				+ "</H2>");
		verticalPanel.add(html);
		JSONObject sensorThresholds = sensor.getThresholds();

		Grid grid = new Grid(sensorThresholds.keySet().size() + 1, 8);
		grid.setBorderWidth(2);
		grid.setCellPadding(2);
		grid.setCellSpacing(2);
		grid.setText(0, 0, "System To Detect");
		grid.setText(0, 1, "Min Freq (Hz)");
		grid.setText(0, 2, "Max Freq (Hz)");
		grid.setText(0, 3, "Channel Count");
		grid.setText(0, 4, "Occupancy Threshold (dBm/Hz)");
		grid.setText(0, 5, "Occupancy Threshold (dBm)");
		grid.setText(0, 6, "Active?");
		grid.setText(0, 7, "Delete Band");
		grid.setBorderWidth(2);
		grid.setCellPadding(2);
		grid.setCellSpacing(2);
		CellFormatter formatter = grid.getCellFormatter();

		for (int i = 0; i < grid.getRowCount(); i++) {
			for (int j = 0; j < grid.getColumnCount(); j++) {
				formatter.setHorizontalAlignment(i, j,
						HasHorizontalAlignment.ALIGN_CENTER);
				formatter.setVerticalAlignment(i, j,
						HasVerticalAlignment.ALIGN_MIDDLE);
			}
		}
		for (int i = 0; i < grid.getColumnCount(); i++) {
			grid.getCellFormatter().setStyleName(0, i, "textLabelStyle");
		}

		int row = 1;
		for (String key : sensorThresholds.keySet()) {
			final SweptFrequencyBand threshold = new SweptFrequencyBand(
					sensorThresholds.get(key).isObject());
			grid.setText(row, 0, threshold.getSystemToDetect());
			grid.setText(row, 1, Long.toString(threshold.getMinFreqHz()));
			grid.setText(row, 2, Long.toString(threshold.getMaxFreqHz()));
			final TextBox channelCountTextBox = new TextBox();
			channelCountTextBox.setText(Long.toString(threshold
					.getChannelCount()));
			channelCountTextBox
					.addValueChangeHandler(new ValueChangeHandler<String>() {

						@Override
						public void onValueChange(ValueChangeEvent<String> event) {
							Long oldValue = Long.parseLong(channelCountTextBox
									.getValue());
							try {
								long newValue = Long.parseLong(event.getValue());
								threshold.setChannelCount((long) newValue);
								Admin.getAdminService().updateSensor(
										sensor.toString(), sensorConfig);
							} catch (Exception ex) {
								Window.alert(ex.getMessage());
								channelCountTextBox.setValue(Double
										.toString(oldValue));
							}
						}

					});
			grid.setWidget(row, 3, channelCountTextBox);

			final TextBox thresholdTextBox = new TextBox();
			thresholdTextBox.setText(Double.toString(threshold
					.getThresholdDbmPerHz()));
			thresholdTextBox
					.addValueChangeHandler(new ValueChangeHandler<String>() {

						@Override
						public void onValueChange(ValueChangeEvent<String> event) {
							Double oldThreshold = Double
									.parseDouble(thresholdTextBox.getValue());
							try {
								double newThreshold = Double.parseDouble(event
										.getValue());
								threshold.setThresholdDbmPerHz(newThreshold);
								Admin.getAdminService().updateSensor(
										sensor.toString(), sensorConfig);
							} catch (Exception ex) {
								Window.alert(ex.getMessage());
								thresholdTextBox.setValue(Double
										.toString(oldThreshold));
							}
						}

					});
			grid.setWidget(row, 4, thresholdTextBox);
			grid.setText(row, 5, Float.toString(threshold.getThresholdDbm()));
			CheckBox activeCheckBox = new CheckBox();
			grid.setWidget(row, 6, activeCheckBox);
			activeCheckBox.setValue(threshold.isActive());
			activeCheckBox
					.addValueChangeHandler(new ValueChangeHandler<Boolean>() {

						@Override
						public void onValueChange(
								ValueChangeEvent<Boolean> event) {

							if (event.getValue()) {
								for (String key : sensor.getThresholds()
										.keySet()) {
									SweptFrequencyBand th = new SweptFrequencyBand(
											sensor.getThreshold(key));
									th.setActive(false);
								}
							}
							threshold.setActive(event.getValue());
							draw();

						}
					});

			Button deleteButton = new Button("Delete Band");
			deleteButton.addClickHandler(new DeleteThresholdClickHandler(
					threshold));
			grid.setWidget(row, 7, deleteButton);
			row++;
		}
		verticalPanel.add(grid);
		HorizontalPanel horizontalPanel = new HorizontalPanel();
		Button addButton = new Button("Add Band");
		addButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				new AddSweptFrequencySensorBand(admin,
						SweptFrequencySensorBands.this, sensorConfig, sensor,
						verticalPanel).draw();

			}
		});
		horizontalPanel.add(addButton);

		Button recomputeButton = new Button("Recompute Occupancies");
		recomputeButton.setTitle("Recomputes per message summary occupancies.");
		recomputeButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				boolean yes = Window
						.confirm("Ensure no users are using the system. This can take a long time. Proceed?");
				if (yes) {

					final HTML html = new HTML(
							"<h3>Recomputing thresholds - this can take a while. Please wait. </h3>");
					verticalPanel.add(html);

					Admin.getAdminService().recomputeOccupancies(
							sensor.getSensorId(),
							new SpectrumBrowserCallback<String>() {

								@Override
								public void onSuccess(String result) {
									verticalPanel.remove(html);

								}

								@Override
								public void onFailure(Throwable throwable) {
									Window.alert("Error communicating with server");
									admin.logoff();

								}
							});
				}
			}
		});
		horizontalPanel.add(recomputeButton);

		Button doneButton = new Button("Done");
		doneButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				sensorConfig.setUpdateFlag(true);
				Admin.getAdminService().updateSensor(sensor.toString(),
						sensorConfig);
			}
		});

		horizontalPanel.add(doneButton);

		Button logoffButton = new Button("Log Off");
		logoffButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}
		});

		horizontalPanel.add(logoffButton);

		verticalPanel.add(horizontalPanel);

	}

}

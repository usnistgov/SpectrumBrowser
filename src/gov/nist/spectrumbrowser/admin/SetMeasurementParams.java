package gov.nist.spectrumbrowser.admin;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

/**
 * Per measurement parameters for the situation when streaming is NOT configured
 * ( and data is posted discretely ).
 * 
 *
 */

public class SetMeasurementParams {

	private Sensor sensor;
	private SensorConfig sensorConfig;
	private Admin admin;
	private VerticalPanel verticalPanel;
	private MeasurementParams measurementParams;

	public SetMeasurementParams(Admin admin, VerticalPanel verticalPanel,
			Sensor sensor, SensorConfig sensorConfig) {
		this.sensor = sensor;
		this.sensorConfig = sensorConfig;
		this.admin = admin;
		this.verticalPanel = verticalPanel;
		this.measurementParams = new MeasurementParams(
				sensor.getMeasurementParams());
	}

	public void draw() {
		// TODO Auto-generated method stub
		HTML html = new HTML("<h2> Measurement parameters for "
				+ sensor.getSensorId() + "</h2>");
		
		verticalPanel.clear();
		verticalPanel.add(html);
		HTML helpText = new HTML ("<h3> Specify the measurement parameters for discrete (http POST) transport. <br/> "
				+ "These MUST match the parameters reported back in the Data message on each HTTP POST </h3>");
		verticalPanel.add(helpText);
		Grid grid = new Grid(3, 2);
		for (int i = 0; i < grid.getRowCount(); i++) {
			grid.getCellFormatter().setStyleName(i, 0, "textLabelStyle");
		}
		grid.setBorderWidth(2);
		grid.setCellPadding(2);
		grid.setCellSpacing(2);
		
		int row = 0;

		
		grid.setText(row, 0, "The measurement duration for the data  [Data.mPar.td] (s)");
		TextBox timePerMeasurement = new TextBox();
		timePerMeasurement.setText(Float.toString(measurementParams.getTimePerSpectrum()));
		timePerMeasurement
				.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						try {
							float tm = Float.parseFloat(event.getValue());
							if (!measurementParams.setTimePerSpectrum(tm)) {
								Window.alert("Please set a value > 0");
							}
						} catch (NumberFormatException nfe) {
							Window.alert("Please enter a valid number");
						}

					}
				});
		grid.setWidget(row, 1, timePerMeasurement);

		row++;
		grid.setText(row, 0, "Number of spectrums posted at a time in each measurement report [Data.nM] (nM) ");
		TextBox measurementsPerAcquisition = new TextBox();
		measurementsPerAcquisition.setText(Integer.toString(measurementParams.getSpectrumsPerMeasurement()));
		measurementsPerAcquisition
				.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						try {
							int nM = Integer.parseInt(event.getValue());
							if (!measurementParams
									.setSpectrumsPerMeasurement(nM)) {
								Window.alert("please set a value > 0 ");
							}
						} catch (NumberFormatException nfe) {
							Window.alert("Please enter a valid number");
						}
					}
				});
		grid.setWidget(row, 1, measurementsPerAcquisition);

		row++;
		grid.setText(row, 0, "Server aggregated spectrogram duration (IGNORED if nM > 1) (s)");
		TextBox spectrogramSize = new TextBox();
		spectrogramSize.setText(Integer.toString(measurementParams.getSpectrogramIntervalSeconds()));
		spectrogramSize.addValueChangeHandler(new ValueChangeHandler<String> () {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				try {
					int size = Integer.parseInt(event.getValue());
					if (!measurementParams.setSpectrogramIntervalSeconds(size)) {
						Window.alert("please set a value > 0");
					}
					
				} catch (NumberFormatException nfe) {
					Window.alert("Please enter a valid number");
				}
				
			}});
		grid.setWidget(row, 1, spectrogramSize);
		
		verticalPanel.add(grid);
	
		
		
		HorizontalPanel hpanel = new HorizontalPanel();
		Button applyButton = new Button("Apply");
		
		hpanel.add(applyButton);
		
		applyButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				
				if (!measurementParams.verify()) {
					Window.alert("Please specify all fields correctly. Capture interval must be > sampling interval.");
					return;
				} else {
					sensorConfig.setUpdateFlag(true);
					Admin.getAdminService().updateSensor(sensor.toString(),
							sensorConfig);
				}
			}} );

		

		Button cancelButton = new Button("Cancel");
		cancelButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				sensorConfig.draw();
			}
		});
		hpanel.add(cancelButton);

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

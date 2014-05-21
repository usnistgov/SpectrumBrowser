package gov.nist.spectrumbrowser.client;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.user.client.ui.HorizontalPanel;
import com.googlecode.gwt.charts.client.ChartLoader;
import com.googlecode.gwt.charts.client.ChartPackage;
import com.googlecode.gwt.charts.client.ColumnType;
import com.googlecode.gwt.charts.client.DataTable;
import com.googlecode.gwt.charts.client.corechart.LineChart;
import com.googlecode.gwt.charts.client.corechart.LineChartOptions;
import com.googlecode.gwt.charts.client.options.HAxis;
import com.googlecode.gwt.charts.client.options.VAxis;

public class PowerSpectrumChart extends HorizontalPanel {
	private String mTitle;
	private long[] mFreq;
	private int[] mPower;

	private LineChart lineChart;

	static Logger logger = Logger.getLogger(SpectrumBrowserService.class
			.getName());

	/**
	 * SpectrumChart
	 * 
	 * @param freq
	 *            - array of frequencies (mhz)
	 * @param power
	 *            - array of power (dbm)
	 * @param minPower
	 *            - min power for the plot
	 * @param maxPower
	 *            - max power for the plot
	 * @param minFreq
	 *            - min freq for the plot
	 * @param maxFreq
	 *            - max freq for the plot
	 * @param width
	 *            - width of the plot
	 * @param height
	 *            - height of the plot
	 */
	public PowerSpectrumChart(String title, long[] freq, int[] power,
			 int width, int height) {
		try {
			
			super.setWidth(width + "px");
			super.setHeight(height + "px");
			this.mTitle = title;
			this.mPower = power;
			this.mFreq = freq;

			ChartLoader chartLoader = new ChartLoader(ChartPackage.CORECHART);
			logger.fine("PowerSpectrumChart : " + title + " freq size "
					+ freq.length + " power " + power.length);
			chartLoader.loadApi(new Runnable() {
				@Override
				public void run() {
					try {
						logger.fine("loaded points into chart");
						lineChart = new LineChart();
						PowerSpectrumChart.this.add(lineChart);

						DataTable dataTable = DataTable.create();
						dataTable.addColumn(ColumnType.NUMBER, " dBm");
						dataTable.addColumn(ColumnType.NUMBER, " Power (dBm)");

						dataTable.addRows(PowerSpectrumChart.this.mFreq.length);
						for (int i = 0; i < mFreq.length; i++ ) {
							dataTable.setValue(i, 0,String.valueOf(mFreq[i]));
						}
						for (int i = 0; i < PowerSpectrumChart.this.mFreq.length; i++) {
							dataTable
									.setValue(
											(int) i,
											1,
											String.valueOf(PowerSpectrumChart.this.mPower[i]));
						}
						LineChartOptions options = LineChartOptions.create();
						options.setBackgroundColor("#f0f0f0");
						options.setTitle(mTitle);
						options.setHAxis(HAxis.create("Frequency (MHz)"));
						options.setVAxis(VAxis.create("Power (dBm)"));
						lineChart.draw(dataTable, options);
						lineChart.setVisible(true);
					} catch (Exception ex) {
						logger.log(Level.SEVERE, "Error drawing chart", ex);
					}

				}
			});
		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Problem loading chart api", ex);
		}
	}

}

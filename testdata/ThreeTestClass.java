public class ThreeTestClass
{
	public ThreeTestClass()
	{
	}
	
	public boolean alwaysTrue()
	{
		return true;
	}
	
	public boolean alwaysFalse()
	{
	    return false;
	}
	
	public int returnInt(int a)
	{
		int b = 0;
	    for(; b < a; b++);
	    return b;
	}
}